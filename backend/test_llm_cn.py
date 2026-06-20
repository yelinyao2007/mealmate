"""Test LLM with Chinese input."""
import sys
import asyncio
import io
from pathlib import Path

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))

from dotenv import load_dotenv
load_dotenv(base_path / ".env")

async def test():
    from app.providers.multi_provider_client import MultiProviderLLMClient
    
    print("1. Creating client...")
    client = MultiProviderLLMClient()
    print(f"   Providers: {list(client._providers.keys())}")
    print(f"   Demo mode: {client._demo_mode_enabled}")
    
    if not client._providers:
        print("ERROR: No providers loaded!")
        return
    
    print("2. Testing chat with Chinese input...")
    result = await client.chat_completion(
        messages=[{"role": "user", "content": "用鸡蛋和西红柿做一道菜"}],
        max_tokens=100
    )
    print(f"3. Success!")
    print(f"   Result: {result}")
    
    print("\n4. Testing English...")
    result2 = await client.chat_completion(
        messages=[{"role": "user", "content": "Make a dish with eggs and tomatoes"}],
        max_tokens=100
    )
    print(f"   English Result: {result2}")

asyncio.run(test())