#!/bin/bash

set -e

echo "=== MealMate 部署脚本 ==="

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "[1/7] 检测系统并安装依赖..."

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "无法检测操作系统"
    exit 1
fi

if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt update
    apt install -y curl git nginx python3 python3-pip python3-venv nodejs npm postgresql postgresql-contrib
elif [ "$OS" = "centos" ] || [ "$OS" = "rocky" ] || [ "$OS" = "alma" ]; then
    yum install -y curl git nginx python3 python3-pip nodejs npm postgresql postgresql-server
fi

echo "[2/7] 配置 PostgreSQL..."
systemctl enable postgresql
systemctl start postgresql

sudo -u postgres psql -c "CREATE DATABASE mealmate;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER mealmate WITH PASSWORD 'mealmate123';" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mealmate TO mealmate;" 2>/dev/null || true

echo "[3/7] 安装后端 Python 依赖..."
cd "$BACKEND_DIR"
pip3 install -r requirements.txt

echo "[4/7] 安装前端 Node 依赖..."
cd "$FRONTEND_DIR"
npm install

echo "[5/7] 构建前端..."
npm run build

echo "[6/7] 配置 Nginx..."

SERVER_IP=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')

cat > /etc/nginx/sites-available/mealmate << EOF
server {
    listen 80;
    server_name $SERVER_IP;

    location / {
        root $FRONTEND_DIR/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/mealmate /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

echo "[7/7] 创建启动脚本..."

cat > "$PROJECT_DIR/scripts/start.sh" << STARTEOF
#!/bin/bash
PROJECT_DIR="$PROJECT_DIR"

echo "启动 MealMate 后端服务..."
cd "$PROJECT_DIR/backend"
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /var/log/mealmate/backend.log 2>&1 &
echo "后端已启动 (PID: $!)"

echo "等待服务就绪..."
sleep 3

echo "服务状态:"
ps aux | grep uvicorn | grep -v grep
STARTEOF

cat > "$PROJECT_DIR/scripts/stop.sh" << STOPEOF
#!/bin/bash
echo "停止 MealMate 服务..."
pkill -f "uvicorn app.main:app" && echo "后端已停止" || echo "后端未运行"
STOPEOF

chmod +x "$PROJECT_DIR/scripts/start.sh"
chmod +x "$PROJECT_DIR/scripts/stop.sh"

echo ""
echo "=== 部署完成 ==="
echo "访问地址: http://$SERVER_IP"
echo ""
echo "启动后端: $PROJECT_DIR/scripts/start.sh"
echo "停止后端: $PROJECT_DIR/scripts/stop.sh"
echo ""
echo "注意: 请先修改 backend/.env 中的数据库连接配置"