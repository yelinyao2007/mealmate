import subprocess
import sys

proc = subprocess.Popen([
    sys.executable, '-m', 'uvicorn', 'app.main:app',
    '--host', '127.0.0.1', '--port', '8000', '--log-level', 'debug'
], cwd=r'D:\OwnProjects\mealmate_y\backend',
   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

# Print output for a few seconds
import time
start = time.time()
while time.time() - start < 8:
    line = proc.stdout.readline()
    if line:
        print(line.decode('utf-8', errors='replace').strip())
    else:
        break

proc.terminate()
proc.wait()
print("Backend terminated")
