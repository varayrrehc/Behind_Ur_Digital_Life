import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'tool_database.db')

if not os.path.exists(db_path):
    print("Database not found!")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT * FROM strength_checks")
    rows = cursor.fetchall()
    
    print("\n" + "="*50)
    print(" 📊 PASSWORD STRENGTH CHECK LOGS")
    print("="*50)
    
    if not rows:
        print("\nNo logs found yet. The database is empty.")
    else:
        for row in rows:
            print(f"[{row[1]}] ID {row[0]} | {row[2]}")
            
    print("\n" + "="*50)
    
except Exception as e:
    print(f"Error reading database: {e}")
finally:
    conn.close()
