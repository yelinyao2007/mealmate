"""Quick test with timeout fix."""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))
load_dotenv(base_path / ".env")

os.environ["SECONDARY_PROVIDER"] = ""
os.environ["TERTIARY_PROVIDER"] = ""

print("[1] Init...", flush=True)
from app.providers.multi_provider_client import MultiProviderLLMClient

client = MultiProviderLLMClient()
print(f"[2] Providers: {list(client._providers.keys())}, demo={client._demo_mode_enabled}", flush=True)

if not client._providers:
    print("[3] NO PROVIDERS!", flush=True)
    sys.exit(1)

# Test directly on provider instead of going through client
print("[3] Test direct...", flush=True)
provider = client._providers["openai"]

async def test():
    return await provider.chat_completion([{"role": "user", "content": "Hi"}], max_tokens=5, temperature=0.7)

result = asyncio.run(test())
print(f"[4] SUCCESS: {result}", flush=True)