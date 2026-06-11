import sqlite3
import os
import json

db_path = os.path.expanduser("~/.phoenix/phoenix.db")
if not os.path.exists(db_path):
    print("No database found.")
else:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, attributes FROM spans WHERE span_kind = 'TOOL' OR name LIKE 'execute_tool%' ORDER BY start_time DESC LIMIT 10")
        for row in cursor.fetchall():
            name = row[0]
            attributes = json.loads(row[1]) if row[1] else {}
            output_val_raw = attributes.get("output", {}).get("value", "")
            print(f"Tool: {name}")
            print(f"Output Raw: {output_val_raw[:200]}")
            print("-" * 50)
