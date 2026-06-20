import sqlite3

conn = sqlite3.connect(r'D:\OwnProjects\mealmate_y\backend\data\mealmate.db')
cursor = conn.cursor()

cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='workflow_executions'")
row = cursor.fetchone()
if row:
    print("Table CREATE SQL:")
    print(row[0])

print("\nAll columns:")
cursor.execute("PRAGMA table_info(workflow_executions)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")

# Also check models.py definition
print("\nComparing with model definition...")
sys_path_backup = sys.path[:]
sys.path.insert(0, r'D:\OwnProjects\mealmate_y\backend')
from app.models import WorkflowExecution
print("Model columns:")
for column in WorkflowExecution.__table__.columns:
    print(f"  {column.name} ({column.type})")
sys.path = sys_path_backup

conn.close()
