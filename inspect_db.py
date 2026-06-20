import sqlite3

conn = sqlite3.connect('backend/data/mealmate.db')
cursor = conn.cursor()

# Get full table schema
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='workflow_executions'")
row = cursor.fetchone()
if row:
    print('Table SQL:')
    print(row[0])

print('\nFull column info:')
cursor.execute("PRAGMA table_info(workflow_executions)")
for col in cursor.fetchall():
    print(f"  cid={col[0]}, name={col[1]}, type={col[2]}, notnull={col[3]}, dflt={col[4]}, pk={col[5]}")

conn.close()
