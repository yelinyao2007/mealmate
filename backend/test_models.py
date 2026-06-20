"""Test different models with Longcat API."""
import os
os.environ["OPENAI_API_KEY"] = "ak_2GY4MN8cl9ho6wW8841wQ1EH3Eg5H"

from openai import OpenAI

client = OpenAI(
    api_key="ak_2GY4MN8cl9ho6wW8841wQ1EH3Eg5H",
    base_url="https://api.longcat.chat/openai",
    max_retries=0
)

# Try different models
models = ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]

for model in models:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say hi"}],
            max_tokens=5
        )
        print(f"{model}: {response.choices[0].message.content}")
    except Exception as e:
        print(f"{model}: {e}")