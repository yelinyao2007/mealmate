import py_compile
import sys

try:
    py_compile.compile('backend/app/routers/ai.py', doraise=True)
    print("OK - No syntax errors")
except py_compile.PyCompileError as e:
    print(f"Syntax error: {e}")
    sys.exit(1)