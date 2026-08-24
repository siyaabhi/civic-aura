"""
Builds civic_aura.db from schema.sql using Python's built-in sqlite3 module.
No separate sqlite3.exe install needed — Python already ships with this.

Run with:
    python build_db.py
"""

import sqlite3
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(HERE, "schema.sql")
DB_PATH = os.path.join(HERE, "civic_aura.db")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("Removed old civic_aura.db so we start fresh.")

with open(SCHEMA_PATH, "r") as f:
    schema_sql = f.read()

conn = sqlite3.connect(DB_PATH)
conn.executescript(schema_sql)
conn.commit()

# Quick sanity check — list tables and show the sample localities
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
print("Tables created:", tables)

cursor.execute("SELECT name, district, aura FROM localities;")
print("\nSample localities:")
for row in cursor.fetchall():
    print(" -", row)

conn.close()
print("\nDone. civic_aura.db is ready in this folder.")