import sqlite3

conn = sqlite3.connect('backend/data/mealmate.db')
cursor = conn.cursor()

# Check workflow_executions table
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='workflow_executions'")
row = cursor.fetchone()
if row:
    print('Table SQL:', row[0])
else:
    print('Table not found')

print('\nColumns:')
cursor.execute("PRAGMA table_info(workflow_executions)")
for col in cursor.fetchall():
    print(col)

conn.close()
