import subprocess
import sys
import os

db_path = 'data/mealmate.db'
cmd = ['sqlite3', db_path, 'ALTER TABLE users ADD COLUMN ai_memory TEXT;']

log_file = 'add_column_log.txt'
with open(log_file, 'w') as f:
    f.write('Running command: ' + ' '.join(cmd) + '\n')
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        f.write('stdout: ' + result.stdout + '\n')
        f.write('stderr: ' + result.stderr + '\n')
        f.write('return code: ' + str(result.returncode) + '\n')
    except Exception as e:
        f.write('Error: ' + str(e) + '\n')
