import sqlite3
import os
import pandas as pd

db_path = os.path.expanduser("~/.phoenix/phoenix.db")
if not os.path.exists(db_path):
    print("No database found.")
else:
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query("SELECT span_id, name, start_time, span_kind, status_code FROM spans ORDER BY start_time DESC", conn)
        print("Total Spans:", len(df))
        print(df.head(20))
