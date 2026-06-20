"""Test API with Chinese."""
import sys
import asyncio
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))

async def test():
    import httpx
    
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=90.0) as client:
        print("1. Login...")
        login_resp = await client.post(
            "/api/auth/login",
            json={"email": "test123@test.com", "password": "test123"}
        )
        print(f"   Status: {login_resp.status_code}")
        
        if login_resp.status_code != 200:
            print(f"   Error: {login_resp.text}")
            return
        
        token = login_resp.json().get("access_token")
        print(f"   Token: {token[:30]}...")
        
        print("\n2. Call agent1 START with Chinese...")
        agent_resp = await client.post(
            "/api/agent1/start",
            json={"ingredients": ["鸡蛋", "西红柿"]},
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"   Status: {agent_resp.status_code}")
        print(f"   Response: {agent_resp.text}")

asyncio.run(test())