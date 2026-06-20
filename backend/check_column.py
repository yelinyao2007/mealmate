import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect

engine = create_engine('sqlite:///data/mealmate.db', connect_args={"check_same_thread": False})
inspector = inspect(engine)
columns = inspector.get_columns('users')
column_names = [c['name'] for c in columns]
print('Columns in users table:', column_names)
if 'ai_memory' in column_names:
    print('ai_memory column exists')
else:
    print('ai_memory column missing')
