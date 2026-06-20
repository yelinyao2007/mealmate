"""Quick test of LLM provider."""
import sys
import asyncio
from pathlib import Path

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))

from dotenv import load_dotenv
load_dotenv(base_path / ".env")

async def test():
    from app.providers.multi_provider_client import MultiProviderLLMClient
    
    print("Creating client...")
    client = MultiProviderLLMClient()
    print(f"Providers: {list(client._providers.keys())}")
    print(f"Demo mode: {client._demo_mode_enabled}")
    
    if "openai" in client._providers:
        print("Testing chat completion...")
        result = await client.chat_completion(
            messages=[{"role": "user", "content": "你好"}],
            max_tokens=50
        )
        print(f"Success! Result: {result}")
    else:
        print("No providers available!")

asyncio.run(test())