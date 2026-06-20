"""Test chat completion sync."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))
load_dotenv(base_path / ".env")

# Fix stdout encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from openai import OpenAI

client = OpenAI(
    api_key="ak_2GY4MN8cl9ho6wW8841wQ1EH3Eg5H",
    base_url="https://api.longcat.chat/openai"
)

response = client.chat.completions.create(
    model="LongCat-Flash-Chat",
    messages=[{"role": "user", "content": "Hi"}],
    max_tokens=10
)
print(f"SUCCESS! Response: {response.choices[0].message.content}")