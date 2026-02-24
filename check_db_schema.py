import sqlite3
import os

db_path = "C:/Users/cisco/Documents/Niru-Predictpath-AI/NiRu-predictpath-tools/VulnIntel/data/db/vuln.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- CVE Table Schema ---")
    cursor.execute("PRAGMA table_info(cve)")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- CWE Table Schema ---")
    cursor.execute("PRAGMA table_info(cwe)")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- KEV Table Schema ---")
    cursor.execute("PRAGMA table_info(kev)")
    for row in cursor.fetchall():
        print(row)
        
    conn.close()
