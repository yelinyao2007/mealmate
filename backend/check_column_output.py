import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///data/mealmate.db', connect_args={"check_same_thread": False})

with engine.connect() as conn:
    result = conn.execute(text("PRAGMA table_info(users);"))
    columns = result.fetchall()
    column_names = [col[1] for col in columns]
    with open('column_check.txt', 'w') as f:
        f.write('Existing columns: ' + str(column_names))
        if 'ai_memory' in column_names:
            f.write('\nai_memory column exists')
        else:
            f.write('\nai_memory column missing')
