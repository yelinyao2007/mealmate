import subprocess
import time
import sys
import urllib.request
import json

# Start backend server
print("Starting backend server...")
backend_proc = subprocess.Popen([
    sys.executable, '-m', 'uvicorn', 'app.main:app',
    '--host', '127.0.0.1', '--port', '8000', '--log-level', 'warning'
], cwd=r'D:\OwnProjects\mealmate_y\backend',
   stdout=subprocess.PIPE, stderr=subprocess.PIPE)

time.sleep(4)

# Test workflow without auth (expect 401)
print("\n1. Testing workflow without auth (expect 401)...")
try:
    url = 'http://localhost:8000/api/workflow/execute'
    payload = json.dumps({
        'workflow_type': 'menu_and_nutrition',
        'num_people': 100,
        'budget_per_meal': 15,
        'season': '春季',
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(f"Unexpected success: {resp.status}")
except urllib.error.HTTPError as e:
    print(f"Got expected HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:100]}")

# Test image recognition
print("\n2. Testing image recognition...")
try:
    img_data = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
    url = 'http://localhost:8000/api/image/recognize'
    payload = json.dumps({
        'image_data': 'data:image/png;base64,' + img_data,
        'recognition_type': 'ingredients'
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"Status: {resp.status}")
        print(f"Ingredients: {data.get('ingredients')}")
except Exception as e:
    print(f"Error: {e}")

# Test workflow types endpoint (public)
print("\n3. Testing workflow types (public)...")
try:
    url = 'http://localhost:8000/api/workflow/types'
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"Status: {resp.status}")
        print(f"Available types: {list(data.keys())}")
except Exception as e:
    print(f"Error: {e}")

# Stop backend
backend_proc.terminate()
backend_proc.wait()
print("\nBackend stopped. Tests complete!")
