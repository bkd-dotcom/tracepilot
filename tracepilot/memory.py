"""SQLite Economic Memory engine for TracePilot."""

import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any

from tracepilot.config import (
    W_SUCCESS, W_COST, W_LATENCY, W_RECOVERY,
    MAX_EXPECTED_COST, MAX_EXPECTED_LATENCY,
    EXPLOIT_THRESHOLD, DEFAULT_TOOL, MODEL_NAME
)


@contextmanager
def get_db(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


def init_db(db_path: str = "tracepilot_memory.db") -> None:
    """Create table if not exists."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS economic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_category TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                model_name TEXT NOT NULL,
                total_runs INTEGER DEFAULT 0,
                successful_runs INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                total_latency REAL DEFAULT 0.0,
                total_recovery_cost REAL DEFAULT 0.0,
                confidence_score REAL DEFAULT 0.5,
                previous_confidence REAL DEFAULT 0.5,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(task_category, tool_name, model_name)
            )
        ''')
        # Simple migration if the column is missing
        try:
            cursor.execute('ALTER TABLE economic_memory ADD COLUMN previous_confidence REAL DEFAULT 0.5')
        except sqlite3.OperationalError:
            pass # Column already exists


def _recalculate_confidence(task_category: str, tool_name: str, model_name: str, cursor) -> float:
    """Calculate the Economic Score."""
    cursor.execute('''
        SELECT total_runs, successful_runs, total_cost, total_latency, total_recovery_cost, confidence_score
        FROM economic_memory
        WHERE task_category = ? AND tool_name = ? AND model_name = ?
    ''', (task_category, tool_name, model_name))
    row = cursor.fetchone()
    
    if not row or row['total_runs'] == 0:
        return 0.5

    total_runs = row['total_runs']
    successful_runs = row['successful_runs']
    old_score = row['confidence_score']
    
    avg_cost = row['total_cost'] / total_runs
    avg_latency = row['total_latency'] / total_runs
    avg_recovery_cost = row['total_recovery_cost'] / total_runs

    success_rate = successful_runs / total_runs
    cost_efficiency = 1.0 - min(avg_cost / MAX_EXPECTED_COST, 1.0)
    latency_efficiency = 1.0 - min(avg_latency / MAX_EXPECTED_LATENCY, 1.0)
    recovery_efficiency = 1.0 - min(avg_recovery_cost / MAX_EXPECTED_COST, 1.0)

    score = (
        W_SUCCESS * success_rate +
        W_COST * cost_efficiency +
        W_LATENCY * latency_efficiency +
        W_RECOVERY * recovery_efficiency
    )
    
    # Ensure score is between 0 and 1
    score = max(0.0, min(1.0, score))
    
    cursor.execute('''
        UPDATE economic_memory
        SET previous_confidence = ?, confidence_score = ?, last_updated = CURRENT_TIMESTAMP
        WHERE task_category = ? AND tool_name = ? AND model_name = ?
    ''', (old_score, score, task_category, tool_name, model_name))
    
    return score


def _recalculate_all(db_path: str = "tracepilot_memory.db") -> None:
    """Recalculate confidence scores for all entries."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT task_category, tool_name, model_name FROM economic_memory')
        rows = cursor.fetchall()
        for row in rows:
            _recalculate_confidence(row['task_category'], row['tool_name'], row['model_name'], cursor)


def record_run(task_category: str, tool_name: str, success: bool, cost: float, latency: float, recovery_cost: float = 0.0, db_path: str = "tracepilot_memory.db") -> None:
    """Insert or update a row."""
    # For MVP we only use gemini-2.5-flash
    model_name = MODEL_NAME
    
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        
        # Upsert logic (insert if not exists, then update)
        cursor.execute('''
            INSERT OR IGNORE INTO economic_memory (task_category, tool_name, model_name)
            VALUES (?, ?, ?)
        ''', (task_category, tool_name, model_name))
        
        cursor.execute('''
            UPDATE economic_memory
            SET total_runs = total_runs + 1,
                successful_runs = successful_runs + ?,
                total_cost = total_cost + ?,
                total_latency = total_latency + ?,
                total_recovery_cost = total_recovery_cost + ?
            WHERE task_category = ? AND tool_name = ? AND model_name = ?
        ''', (1 if success else 0, cost, latency, recovery_cost, task_category, tool_name, model_name))
        
        _recalculate_confidence(task_category, tool_name, model_name, cursor)


def get_optimal_routing(task_category: str, db_path: str = "tracepilot_memory.db") -> Dict[str, Any]:
    """Returns optimal routing decision."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT tool_name, model_name, confidence_score, successful_runs, total_runs, total_cost, total_recovery_cost
            FROM economic_memory
            WHERE task_category = ?
            ORDER BY confidence_score DESC
        ''', (task_category,))
        rows = cursor.fetchall()

    all_options = []
    for r in rows:
        avg_cost = r['total_cost'] / r['total_runs'] if r['total_runs'] > 0 else 0
        avg_rec_cost = r['total_recovery_cost'] / r['total_runs'] if r['total_runs'] > 0 else 0
        success_rate = (r['successful_runs'] / r['total_runs'] * 100) if r['total_runs'] > 0 else 0
        
        all_options.append({
            "tool": r['tool_name'],
            "confidence": round(r['confidence_score'], 2),
            "success_rate": round(success_rate, 1),
            "avg_cost": avg_cost,
            "avg_recovery_cost": avg_rec_cost
        })

    if not rows:
        return {
            "tool": DEFAULT_TOOL,
            "confidence": 0.5,
            "mode": "explore",
            "all_options": []
        }

    best_option = rows[0]
    confidence = best_option['confidence_score']
    
    if confidence >= EXPLOIT_THRESHOLD:
        mode = "exploit"
        selected_tool = best_option['tool_name']
    else:
        mode = "explore"
        # Cycle through all available tools to ensure we explore everything
        all_possible_tools = ["web_search", "uploaded_documents", "internal_kb"]
        # Find tools we haven't tried yet, or pick the one with the fewest runs
        tried_tools = {r['tool_name']: r['total_runs'] for r in rows}
        
        # Tools not in DB have 0 runs
        untried = [t for t in all_possible_tools if t not in tried_tools]
        if untried:
            selected_tool = untried[0]
        else:
            # If all tried, pick the one that ISN'T the currently failing best_option
            # Just rotate: internal_kb -> web_search -> uploaded_documents -> internal_kb
            idx = all_possible_tools.index(best_option['tool_name'])
            selected_tool = all_possible_tools[(idx + 1) % len(all_possible_tools)]

    return {
        "tool": selected_tool,
        "confidence": confidence,
        "mode": mode,
        "all_options": all_options
    }


def get_confidence_table(db_path: str = "tracepilot_memory.db") -> List[Dict[str, Any]]:
    """Returns all rows for display."""
    init_db(db_path)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM economic_memory ORDER BY task_category, confidence_score DESC
        ''')
        rows = cursor.fetchall()
        
    result = []
    for r in rows:
        total_runs = r['total_runs']
        avg_cost = r['total_cost'] / total_runs if total_runs > 0 else 0.0
        avg_latency = r['total_latency'] / total_runs if total_runs > 0 else 0.0
        avg_recovery = r['total_recovery_cost'] / total_runs if total_runs > 0 else 0.0
        
        success_rate = r['successful_runs'] / total_runs if total_runs > 0 else 0.0
        
        try:
            prev_conf = r['previous_confidence']
        except (IndexError, KeyError):
            prev_conf = 0.5
        
        result.append({
            "category": r['task_category'],
            "tool": r['tool_name'],
            "runs": total_runs,
            "success_rate": success_rate,
            "confidence": r['confidence_score'],
            "previous_confidence": prev_conf,
            "delta": r['confidence_score'] - prev_conf,
            "avg_cost": avg_cost,
            "avg_latency": avg_latency,
            "avg_recovery": avg_recovery
        })
    return result


def update_confidence_from_audit(task_category: str, tool_name: str, new_confidence: float, db_path: str = "tracepilot_memory.db") -> None:
    """Direct confidence update from the auditor."""
    model_name = MODEL_NAME
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE economic_memory
            SET previous_confidence = confidence_score, confidence_score = ?, last_updated = CURRENT_TIMESTAMP
            WHERE task_category = ? AND tool_name = ? AND model_name = ?
        ''', (new_confidence, task_category, tool_name, model_name))


def reset_db(db_path: str = "tracepilot_memory.db") -> None:
    """Drop and recreate the table."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS economic_memory')
        cursor.execute('CREATE TABLE IF NOT EXISTS system_config (key TEXT PRIMARY KEY, value TEXT)')
        import datetime
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute('INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)', ('last_reset', now_iso))
    init_db(db_path)

def get_last_reset_time(db_path: str = "tracepilot_memory.db") -> str:
    """Get the ISO timestamp of the last system reset."""
    try:
        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM system_config WHERE key = ?', ('last_reset',))
            row = cursor.fetchone()
            if row:
                return row[0]
    except Exception:
        pass
    return "1970-01-01T00:00:00+00:00"
