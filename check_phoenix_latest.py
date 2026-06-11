import sqlite3
import os

db_path = os.path.expanduser("~/.phoenix/phoenix.db")
if not os.path.exists(db_path):
    print("No database found.")
else:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT span_id, name, start_time FROM spans WHERE span_kind = 'TOOL' OR name LIKE 'execute_tool%' ORDER BY id DESC LIMIT 5")
        for row in cursor.fetchall():
            print(row)
