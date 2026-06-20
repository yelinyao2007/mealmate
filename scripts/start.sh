#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "启动 MealMate 后端服务..."

cd "$PROJECT_DIR/backend"
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /var/log/mealmate/backend.log 2>&1 &
echo "后端已启动 (PID: $!)"

echo ""
echo "服务状态:"
ps aux | grep uvicorn | grep -v grep