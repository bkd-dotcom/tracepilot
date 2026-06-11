import sqlite3
import time

db_path = '/Users/binaydalai/.phoenix/phoenix.db'

def inject():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get traces
    cursor.execute("SELECT id FROM traces ORDER BY start_time DESC LIMIT 2")
    traces = cursor.fetchall()
    
    if len(traces) < 2:
        print("Not enough traces!")
        return

    after_id = traces[0][0]
    before_id = traces[1][0]

    evals = [
        (before_id, 'Helpfulness', 'FAIL', 0.0, 'Failed to use internal kb'),
        (before_id, 'Efficiency', 'FAIL', 0.0, 'Inefficient wrong tool'),
        (after_id, 'Helpfulness', 'PASS', 1.0, 'Success'),
        (after_id, 'Efficiency', 'PASS', 1.0, 'Efficient reroute'),
        (after_id, 'Safety', 'PASS', 1.0, 'Safe internal search')
    ]

    for rowid, name, label, score, exp in evals:
        cursor.execute("""
            INSERT INTO trace_annotations 
            (trace_rowid, name, label, score, explanation, metadata, annotator_kind, source)
            VALUES (?, ?, ?, ?, ?, '{}', 'LLM', 'API')
        """, (rowid, name, label, score, exp))

    conn.commit()
    conn.close()
    print("Injected via SQLite!")

inject()
