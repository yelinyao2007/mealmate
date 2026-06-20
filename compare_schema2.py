import sqlite3
import sys

conn = sqlite3.connect(r'D:\OwnProjects\mealmate_y\backend\data\mealmate.db')
cursor = conn.cursor()

print("Current table columns:")
cursor.execute("PRAGMA table_info(workflow_executions)")
cols = {}
for col in cursor.fetchall():
    cols[col[1]] = col[2]
    print(f"  {col[1]} ({col[2]})")

print("\nModel expected columns:")
sys_path_backup = sys.path[:]
sys.path.insert(0, r'D:\OwnProjects\mealmate_y\backend')
from app.models import WorkflowExecution
for column in WorkflowExecution.__table__.columns:
    print(f"  {column.name} ({column.type})")
    if column.name not in cols:
        print(f"    *** MISSING IN DATABASE ***")

conn.close()
sys.path = sys_path_backup