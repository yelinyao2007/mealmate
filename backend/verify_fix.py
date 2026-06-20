import sqlite3
import os

db_path = os.path.join('data', 'mealmate.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(users);")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]
conn.close()

with open('verify_result.txt', 'w') as f:
    f.write('Columns: ' + ', '.join(column_names) + '\n')
    if 'ai_memory' in column_names:
        f.write('SUCCESS: ai_memory column exists\n')
    else:
        f.write('FAIL: ai_memory column missing\n')
