"""Test multi_provider_client - simplified."""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))
load_dotenv(base_path / ".env")

print("1. Creating client...")
from app.providers.multi_provider_client import MultiProviderLLMClient
client = MultiProviderLLMClient()
print(f"   Providers: {list(client._providers.keys())}")
print(f"   Demo mode: {client._demo_mode_enabled}")

if client._providers:
    print("2. Testing chat...")
    provider = list(client._providers.values())[0]
    print(f"   Provider: {provider}")
    
    async def test():
        result = await provider.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10
        )
        return result
    
    result = asyncio.run(test())
    print(f"   SUCCESS! Result: {result}")
else:
    print("   No providers loaded!")