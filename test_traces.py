import sqlite3
import pandas as pd
import json
import os

db_path = os.path.expanduser("~/.phoenix/phoenix.db")
conn = sqlite3.connect(db_path)
df = pd.read_sql_query("SELECT start_time FROM spans LIMIT 5", conn)
print(df)
