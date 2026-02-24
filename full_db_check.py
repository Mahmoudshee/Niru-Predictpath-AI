import sqlite3
import os

db_path = "C:/Users/cisco/Documents/Niru-Predictpath-AI/NiRu-predictpath-tools/VulnIntel/data/db/vuln.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Tables ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for t in tables:
        print(t[0])
        
    for t in tables:
        tname = t[0]
        print(f"\n--- {tname} Schema ---")
        cursor.execute(f"PRAGMA table_info({tname})")
        for row in cursor.fetchall():
            print(row)
        
    conn.close()
