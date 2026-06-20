"""Test multi_provider_client."""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Fix stdout encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))
load_dotenv(base_path / ".env")

print("1. Initializing multi_provider_client...")
from app.providers.multi_provider_client import MultiProviderLLMClient

client = MultiProviderLLMClient()
print(f"   Providers: {list(client._providers.keys())}")
print(f"   Demo mode: {client._demo_mode_enabled}")

async def test():
    print("2. Calling chat_completion...")
    result = await client.chat_completion(
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=10
    )
    print(f"   SUCCESS! Result: {result}")
    return result

asyncio.run(test())