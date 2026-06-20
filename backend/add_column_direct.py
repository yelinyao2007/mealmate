import sqlite3
import os

db_path = os.path.join('data', 'mealmate.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if column exists
cursor.execute("PRAGMA table_info(users);")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]
if 'ai_memory' not in column_names:
    cursor.execute("ALTER TABLE users ADD COLUMN ai_memory TEXT;")
    conn.commit()
    print('Column added')
else:
    print('Column already exists')
conn.close()
