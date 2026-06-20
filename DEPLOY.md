# MealMate 部署指南

## 环境要求

- Ubuntu 22.04 / CentOS 8
- Node.js 18+
- Python 3.12
- PostgreSQL 14+

## 技术栈

- 前端: React 18 + Vite + TailwindCSS
- 后端: FastAPI + SQLAlchemy
- 数据库: PostgreSQL

## 部署步骤

### 方式一：自动部署（推荐）

1. 上传项目到服务器
```bash
scp -r mealmate_y user@服务器IP:~/
```

2. 执行部署脚本
```bash
cd ~/mealmate_y
chmod +x deploy.sh
sudo ./deploy.sh
```

3. 配置环境变量
```bash
cp backend/.env.example backend/.env
nano backend/.env
```

4. 启动服务
```bash
./scripts/start.sh
```

### 方式二：手动部署

#### 1. 安装依赖
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y curl git nginx python3 python3-pip nodejs npm postgresql postgresql-contrib

# CentOS
sudo yum install -y curl git nginx python3 python3-pip nodejs npm postgresql postgresql-server
```

#### 2. 配置 PostgreSQL
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE mealmate;
CREATE USER mealmate WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE mealmate TO mealmate;
\q
```

#### 3. 配置后端
```bash
cd ~/mealmate_y/backend
cp .env.example .env
nano .env

# 修改 DATABASE_URL 为:
# DATABASE_URL=postgresql://mealmate:yourpassword@localhost:5432/mealmate
```

#### 4. 安装后端依赖
```bash
pip3 install -r requirements.txt
```

#### 5. 构建前端
```bash
cd ~/mealmate_y/frontend
npm install
npm run build
```

#### 6. 启动后端服务
```bash
cd ~/mealmate_y/backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

#### 7. 配置 Nginx
```bash
sudo nano /etc/nginx/sites-available/mealmate
```

添加配置：
```nginx
server {
    listen 80;
    server_name 你的服务器IP或域名;

    location / {
        root /root/mealmate_y/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/mealmate /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 使用 systemd 管理（生产环境推荐）

1. 复制服务文件
```bash
sudo cp systemd/mealmate.service /etc/systemd/system/
```

2. 启动服务
```bash
sudo systemctl daemon-reload
sudo systemctl enable mealmate
sudo systemctl start mealmate
```

3. 查看状态
```bash
sudo systemctl status mealmate
```

## 常用命令

```bash
# 启动服务
./scripts/start.sh

# 停止服务
./scripts/stop.sh

# 查看后端日志
tail -f /var/log/mealmate/backend.log

# 重启 Nginx
sudo systemctl restart nginx

# 重启后端
sudo systemctl restart mealmate
```

## 端口说明

- 80: Nginx (前端)
- 8000: FastAPI (后端)
- 5432: PostgreSQL

## 注意事项

1. 修改 `backend/.env` 中的 `JWT_SECRET` 为随机字符串
2. 生产环境建议使用 HTTPS
3. 定期备份 PostgreSQL 数据库
