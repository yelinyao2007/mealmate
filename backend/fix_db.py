import sqlite3

conn = sqlite3.connect('data/mealmate.db')
cursor = conn.cursor()

# Add missing columns to recipes table
try:
    cursor.execute('ALTER TABLE recipes ADD COLUMN is_agent_generated BOOLEAN DEFAULT 0')
    print('Added is_agent_generated column')
except Exception as e:
    print(f'is_agent_generated: {e}')

try:
    cursor.execute('ALTER TABLE recipes ADD COLUMN source_agent VARCHAR(50) DEFAULT ""')
    print('Added source_agent column')
except Exception as e:
    print(f'source_agent: {e}')

try:
    cursor.execute('ALTER TABLE recipes ADD COLUMN remix_parent_id INTEGER')
    print('Added remix_parent_id column')
except Exception as e:
    print(f'remix_parent_id: {e}')

try:
    cursor.execute('ALTER TABLE recipes ADD COLUMN cook_time_minutes INTEGER DEFAULT 0')
    print('Added cook_time_minutes column')
except Exception as e:
    print(f'cook_time_minutes: {e}')

try:
    cursor.execute('ALTER TABLE recipes ADD COLUMN prep_time_minutes INTEGER DEFAULT 0')
    print('Added prep_time_minutes column')
except Exception as e:
    print(f'prep_time_minutes: {e}')

try:
    cursor.execute('ALTER TABLE recipes ADD COLUMN difficulty VARCHAR(50) DEFAULT ""')
    print('Added difficulty column')
except Exception as e:
    print(f'difficulty: {e}')

try:
    cursor.execute('ALTER TABLE recipes ADD COLUMN tip TEXT DEFAULT ""')
    print('Added tip column')
except Exception as e:
    print(f'tip: {e}')

conn.commit()
print('Done!')