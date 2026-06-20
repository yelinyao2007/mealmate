"""Test multi_provider_client - with debug."""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore")

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))
load_dotenv(base_path / ".env")

# Override enabled providers to only openai
os.environ["SECONDARY_PROVIDER"] = ""
os.environ["TERTIARY_PROVIDER"] = ""

print("1. Creating client...")
from app.providers.multi_provider_client import MultiProviderLLMClient
client = MultiProviderLLMClient()
print(f"   Providers: {list(client._providers.keys())}")
print(f"   Demo mode: {client._demo_mode_enabled}")

if "openai" in client._providers:
    print("2. Testing via client.chat_completion...")
    
    async def test():
        result = await client.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10
        )
        return result
    
    result = asyncio.run(test())
    print(f"   SUCCESS! Result: {result}")
else:
    print("   No openai provider!")