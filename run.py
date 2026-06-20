"""Run MealMate from the project root."""
import sys
import os

# Prefer OPENAI as the default provider when launching via run.py
os.environ.setdefault('PRIMARY_PROVIDER', 'openai')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True, reload_dirs=["backend"])
