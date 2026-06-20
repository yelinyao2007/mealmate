import sqlite3

conn = sqlite3.connect('backend/data/mealmate.db')
cursor = conn.cursor()

# Check if output_data column exists
cursor.execute("PRAGMA table_info(workflow_executions)")
columns = [col[1] for col in cursor.fetchall()]

if 'output_data' not in columns:
    print("Adding output_data column...")
    cursor.execute("ALTER TABLE workflow_executions ADD COLUMN output_data JSON")
    conn.commit()
    print("Column added successfully!")
else:
    print("output_data column already exists")

# Verify
cursor.execute("PRAGMA table_info(workflow_executions)")
print("\nCurrent columns:")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")

conn.close()
