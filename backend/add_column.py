import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///data/mealmate.db', connect_args={"check_same_thread": False})

# Check if column exists
with engine.connect() as conn:
    result = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='users';"))
    sql = result.fetchone()
    if sql:
        print('Current users table schema:', sql[0])
    else:
        print('users table not found')

    # Check for ai_memory column
    result = conn.execute(text("PRAGMA table_info(users);"))
    columns = result.fetchall()
    column_names = [col[1] for col in columns]
    print('Existing columns:', column_names)
    if 'ai_memory' not in column_names:
        print('Adding ai_memory column...')
        conn.execute(text("ALTER TABLE users ADD COLUMN ai_memory TEXT;"))
        conn.commit()
        print('Column added.')
    else:
        print('Column already exists.')
