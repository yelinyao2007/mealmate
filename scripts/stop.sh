#!/bin/bash

echo "停止 MealMate 服务..."

pkill -f "uvicorn app.main:app" && echo "后端已停止" || echo "后端未运行"

echo "服务已停止"