"""Test with httpx directly."""
import os
import sys
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))
load_dotenv(base_path / ".env")

async def test():
    print("[1] Creating client...", flush=True)
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("[2] Sending request...", flush=True)
        resp = await client.post(
            "https://api.longcat.chat/openai/v1/chat/completions",
            json={
                "model": "LongCat-Flash-Chat",
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5
            },
            headers={
                "Authorization": "Bearer ak_2GY4MN8cl9ho6wW8841wQ1EH3Eg5H",
                "Content-Type": "application/json"
            }
        )
        print(f"[3] Status: {resp.status_code}", flush=True)
        data = resp.json()
        print(f"[4] Result: {data['choices'][0]['message']['content']}", flush=True)

asyncio.run(test())