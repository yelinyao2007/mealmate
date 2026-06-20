import sqlite3

conn = sqlite3.connect(r'D:\OwnProjects\mealmate_y\backend\data\mealmate.db')
cursor = conn.cursor()

# Check if steps_count exists
cursor.execute("PRAGMA table_info(workflow_executions)")
columns = [col[1] for col in cursor.fetchall()]

if 'steps_count' not in columns:
    print("Adding steps_count column...")
    cursor.execute("ALTER TABLE workflow_executions ADD COLUMN steps_count INTEGER DEFAULT 0")
    conn.commit()
    print("Column added!")
else:
    print("steps_count already exists")

# Verify
cursor.execute("PRAGMA table_info(workflow_executions)")
print("\nCurrent columns:")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")

conn.close()
