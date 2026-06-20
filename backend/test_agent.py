"""Quick test of agent1 API."""
import urllib.request
import urllib.error
import json

# Login first
login_data = json.dumps({"email": "test@test.com", "password": "test123"}).encode('utf-8')
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/auth/login",
    data=login_data,
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        result = json.loads(resp.read().decode())
        token = result.get("access_token")
        print(f"Token: {token[:20]}...")
        
        # Test agent1
        agent_data = json.dumps({"ingredients": ["鸡蛋", "西红柿"]}).encode('utf-8')
        req2 = urllib.request.Request(
            "http://127.0.0.1:8000/api/agent1/start",
            data=agent_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        
        with urllib.request.urlopen(req2, timeout=30) as resp2:
            result2 = json.loads(resp2.read().decode())
            print(f"Success! Reply: {result2.get('reply', '')[:200]}...")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.read().decode()}")
except Exception as e:
    print(f"Error: {e}")