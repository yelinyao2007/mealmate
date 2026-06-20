from pathlib import Path
from dotenv import load_dotenv

# Test path resolution
base_path = Path(__file__).parent
env_path = base_path / ".env"
if env_path.exists():
    load_dotenv(env_path)

print(f"Env path: {env_path}, exists: {env_path.exists()}")
print(f"PRIMARY_PROVIDER: {__import__('os').environ.get('PRIMARY_PROVIDER')}")
print(f"OPENAI_API_KEY: {__import__('os').environ.get('OPENAI_API_KEY', '')[:10]}...")

# Test provider path
pf = base_path / "app" / "providers" / "openai" / "provider.py"
print(f"Provider exists: {pf.exists()}, path: {pf}")