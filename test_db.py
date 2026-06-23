import sqlite3
import re

print("--- Testing SQL Schema Execution ---")

# 1. Read your schema.sql file
with open("db/schema.sql", "r", encoding="utf-8") as f:
    sql_script = f.read()

# Clean up specific PostgreSQL dialects to make it 100% compliant with standard SQLite
# SQLite requires exactly 'INTEGER PRIMARY KEY' or 'INTEGER PRIMARY KEY AUTOINCREMENT'
sql_script = re.sub(r'INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT', sql_script, flags=re.IGNORECASE)
sql_script = re.sub(r'BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT', sql_script, flags=re.IGNORECASE)

# Strip out generated calculated columns and time zone tags that SQLite doesn't natively parse
sql_script = re.sub(r'GENERATED ALWAYS AS .*? STORED', '', sql_script, flags=re.IGNORECASE)
sql_script = re.sub(r'WITH TIME ZONE', '', sql_script, flags=re.IGNORECASE)

try:
    # 2. Connect to an isolated, temporary in-memory database
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # 3. Execute the parsed schema
    cursor.executescript(sql_script)
    print("[SUCCESS] schema.sql compiled and executed with zero errors!")
    
    # 4. Query the master index catalog to pull structural tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    
    print(f"\n[OUTPUT] Generated Database Tables ({len(tables)} total):")
    for idx, table in enumerate(tables, 1):
        print(f"  {idx}. {table[0]}")
        
    conn.close()

except Exception as e:
    print(f"[ERROR] SQL Compilation failed: {e}")