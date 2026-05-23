#!/bin/bash
# 开发启动脚本
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== 编译前端 ==="
cd "$PROJECT_DIR"
npx vite build

echo ""
echo "=== 启动桌面应用 ==="
cd "$PROJECT_DIR"
python3 run.py
