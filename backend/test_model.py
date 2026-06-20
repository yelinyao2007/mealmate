"""Test LongCat-Flash-Chat model."""
from openai import OpenAI

client = OpenAI(
    api_key="ak_2GY4MN8cl9ho6wW8841wQ1EH3Eg5H",
    base_url="https://api.longcat.chat/openai",
    max_retries=0
)

try:
    response = client.chat.completions.create(
        model="LongCat-Flash-Chat",
        messages=[{"role": "user", "content": "Say hello in one word"}],
        max_tokens=10
    )
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")