"""Final test with encoding fix."""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Fix encoding FIRST
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))
load_dotenv(base_path / ".env")

os.environ["SECONDARY_PROVIDER"] = ""
os.environ["TERTIARY_PROVIDER"] = ""

print("[1] Init...", flush=True)
from app.providers.multi_provider_client import MultiProviderLLMClient
client = MultiProviderLLMClient()
print(f"[2] Providers: {list(client._providers.keys())}, demo={client._demo_mode_enabled}", flush=True)

if "openai" not in client._providers:
    print("[ERROR] No openai provider!", flush=True)
    sys.exit(1)

print("[3] Test chat...", flush=True)

async def test():
    return await client.chat_completion([{"role": "user", "content": "Hi"}], max_tokens=10)

result = asyncio.run(test())
print(f"[4] SUCCESS: {result}", flush=True)