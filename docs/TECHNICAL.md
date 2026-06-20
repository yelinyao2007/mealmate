# MealMate 技术文档

## 一、项目概述

### 1.1 产品定位

MealMate（智膳）是一款 AI 驱动的智能食谱应用，旨在帮助用户减少食物浪费、吃得更好。用户只需输入现有食材，AI 即可在几秒钟内生成个性化食谱。

### 1.2 核心功能

| 功能 | 描述 |
|------|------|
| AI 食谱生成 | 输入食材，即刻获得 2-3 个创意食谱 |
| 对话式定制 | 与 AI 聊天修改食谱（"做成素的"、"15分钟内"） |
| 社交动态 | 发布、点赞、评论、收藏食谱 |
| 混搭创作 |Fork 他人食谱并进行二次创作 |
| 智能购物 | 一键购买缺失食材 |
| 用户画像 | 饮食偏好、过敏原、厨艺水平、偏好菜系 |
| 通知中心 | 点赞、评论、混搭通知 |
| 图像识别 | 上传食材图片，AI 自动识别并生成食谱 |
| 多语言 | 支持中文、英文双语切换 |
| 工作流 | 可视化 AI 工作流编排 |

---

## 二、技术架构

### 2.1 系统架构图

```
┌─────────────────┐     ┌─────────────────┐
│   Vercel (SPA)  │     │  Railway (API)  │
│   前端静态托管  │────▶│   Python后端    │
│  mealmate-app   │     │  reasonable-... │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    │                         │
               ┌────▼────┐              ┌─────▼─────┐
               │ SQLite  │              │  Longcat  │
               │ 数据库  │              │  AI 服务  │
               └─────────┘              └───────────┘
```

### 2.2 技术选型

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端框架 | React | 18.3.1 |
| 构建工具 | Vite | 5.3.1 |
| UI 框架 | TailwindCSS | 3.4.4 |
| 路由 | React Router | 6.24.0 |
| HTTP 客户端 | Axios | 1.7.2 |
| 后端框架 | FastAPI | 0.111.0 |
| ASGI 服务器 | Uvicorn | 0.30.1 |
| ORM | SQLAlchemy | 2.0.30 |
| 数据验证 | Pydantic | 2.7.4 |
| 数据库 | SQLite | - |
| AI 提供商 | OpenAI / Longcat | - |
| 部署（前端）| Vercel | - |
| 部署（后端）| Railway | - |

### 2.3 项目结构

```
mealmate/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py           # 配置管理
│   │   ├── database.py        # SQLAlchemy + 迁移
│   │   ├── models.py          # 数据模型
│   │   ├── schemas.py        # Pydantic 模型
│   │   ├── auth.py           # JWT 认证
│   │   ├── routers/
│   │   │   ├── auth.py       # 注册/登录
│   │   │   ├── users.py      # 用户管理
│   │   │   ├── recipes.py    # 食谱 CRUD
│   │   │   ├── ai.py        # AI 对话
│   │   │   ├── social.py    # 社交功能
│   │   │   ├── bookmarks.py # 收藏
│   │   │   ├── notifications.py # 通知
│   │   │   ├── workflow.py # 工作流
│   │   │   ├── agent1.py   # Agent 1
│   │   │   ├── agent2.py   # Agent 2
│   │   │   ├── agent3.py   # Agent 3
│   │   │   ├── i18n.py     # 国际化
│   │   │   └── image_recognition.py # 图像识别
│   │   ├── providers/       # AI 多提供商
│   │   └── static/         # 静态文件
│   ├── .env               # 环境变量
│   ├── requirements.txt    # Python 依赖
│   └── railway.json       # Railway 配置
├── frontend/
│   ├── src/
│   │   ├── pages/           # 页面组件
│   │   │   ├── Landing.jsx  #  landing 页
│   │   │   ├── Login.jsx   #  登录页
│   │   │   ├── Register.jsx #  注册页
│   │   │   ├── Feed.jsx    #  动态页
│   │   │   ├── Recipe.jsx  #  食谱详情
│   │   │   ├── Create.jsx  #  创建食谱
│   │   │   ├── Profile.jsx  #  个人资料
│   │   │   ├── AIChat.jsx  #  AI 聊天
│   │   │   ├── ImageRecog.jsx # 图像识别
│   │   │   ├── Workflow.jsx  # 工作流
│   │   │   ├── Saved.jsx    #  收藏页
│   │   │   └── Notifications.jsx # 通知页
│   │   ├── components/     # 可复用组件
│   │   ├── context/        # React Context
│   │   │   └── AuthContext.jsx
│   │   ├── api.js          # Axios 配置
│   │   ├── App.jsx        # 路由配置
│   │   ├── i18n/          # 国际化
│   │   │   ├── zh.js       # 中文
│   │   │   └── en.js      # 英文
│   │   └── index.css       # TailwindCSS
│   ├── package.json
│   ├── vite.config.js
│   └── vercel.json        # Vercel 配置
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 三、数据库设计

### 3.1 用户表 (users)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | INTEGER | 主键 |
| email | VARCHAR(255) | 唯一邮箱 |
| password_hash | VARCHAR(255) | bcrypt 加密密码 |
| name | VARCHAR(255) | 用户名 |
| avatar_url | VARCHAR(500) | 头像 URL |
| preferences | JSON | 偏好设置 |
| language | VARCHAR(10) | 语言 (en/zh) |
| created_at | DATETIME | 创建时间 |

### 3.2 食谱表 (recipes)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | INTEGER | 主键 |
| user_id | INTEGER | 作者 ID |
| title | VARCHAR(255) | 食谱标题 |
| description | TEXT | 描述 |
| ingredients | JSON | 食材列表 |
| steps | JSON | 烹饪步骤 |
| image_url | VARCHAR(500) | 封面图 |
| likes_count | INTEGER | 点赞数 |
| comments_count | INTEGER | 评论数 |
| is_agent_generated | BOOLEAN | AI 生成标记 |
| source_agent | VARCHAR(50) | 来源 Agent |
| remix_parent_id | INTEGER | 混搭父食谱 |
| cook_time_minutes | INTEGER | 烹饪时间 |
| prep_time_minutes | INTEGER | 准备时间 |
| difficulty | VARCHAR(50) | 难度 |
| tip | TEXT | 小贴士 |
| created_at | DATETIME | 创建时间 |

### 3.3 社交互动表

| 表名 | 字段 |
|------|------|
| likes | user_id, recipe_id |
| comments | user_id, recipe_id, content |
| bookmarks | user_id, recipe_id |
| followers | follower_id, following_id |
| chat_sessions | user_id, current_recipe_id, agent_type |
| chat_messages | session_id, role, content |

---

## 四、API 接口

### 4.1 认证接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/auth/register | 注册用户 |
| POST | /api/auth/login | 登录 |
| GET | /api/auth/me | 当前用户 |
| PUT | /api/auth/me | 更新资料 |

### 4.2 食谱接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/recipes/feed | 食谱流 |
| POST | /api/recipes | 创建食谱 |
| GET | /api/recipes/{id} | 食谱详情 |
| PUT | /api/recipes/{id} | 更新食谱 |
| DELETE | /api/recipes/{id} | 删除食谱 |
| POST | /api/recipes/{id}/like | 点赞/取消 |
| POST | /api/recipes/{id}/comments | 评论 |

### 4.3 AI 接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/ai/generate | 生成食谱 |
| POST | /api/ai/chat/{session_id} | AI 对话 |
| POST | /api/ai/workflow | 工作流执行 |
| POST | /api/image/recognize | 图像识别 |

---

## 五、部署配置

### 5.1 前端部署 (Vercel)

```json
// frontend/vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://reasonable-recreation-production.up.railway.app/api/:path*" }
  ]
}
```

### 5.2 后端部署 (Railway)

```json
// backend/railway.json
{
  "build": {
    "builder": "NIXPACKSBUILDER_BITNAMI_PYTHON",
    "buildPack": "pip",
    "start": "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## 六、快速体验

### 6.1 在线体验

**前端地址**: https://mealmate-app-phi.vercel.app/

**后端地址**: https://reasonable-recreation-production.up.railway.app/

### 6.2 本地运行

```bash
# 1. 克隆项目
git clone https://github.com/yaoyelin2007-bit/mealmate.git
cd mealmate

# 2. 启动后端
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. 启动前端 (新终端)
cd frontend
npm install
npm run dev

# 4. 访问
# 前端: http://localhost:5173
# 后端: http://localhost:8000
```

### 6.3 Docker 一键启动

```bash
# 构建并运行
docker build -t mealmate .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key mealmate

# 访问 http://localhost:8000
```

### 6.4 快速功能测试

```bash
# 注册用户
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test User"}'

# 登录获取 Token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# 生成食谱 (替换 YOUR_TOKEN)
curl -X POST http://localhost:8000/api/ai/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"ingredients":["鸡蛋","番茄","葱"],"preferences":"简单快手"}'

# 查看食谱流
curl http://localhost:8000/api/recipes/feed \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 七、功能截图说明

### 7.1 Landing 页
- 品牌标语："减少食物浪费，吃得更好"
- CTA 按钮："开始做菜"
- 三大功能展示：AI 食谱、社区混搭、智能购物

### 7.2 食谱生成
- 输入食材（支持多语言）
- 选择偏好（素食、低卡、快速等）
- AI 生成 2-3 个食谱卡片

### 7.3 AI 对话
- 会话式修改食谱
- 支持追问调整
- 保存为私人食谱

### 7.4 社交动态
- 瀑布流展示
- 点赞、评论、混搭
- 个人收藏页

### 7.5 工作流
- 可视化节点编排
- 支持 Agent 1/2/3
- 实时执行状态

---

## 八、常见问题

### 8.1 注册失败
- 检查 Railway 后端日志确认服务正常
- 确认密码长度 >= 6 位

### 8.2 AI 生成失败
- 确认 .env 中的 AI API KEY
- 检查 Longcat 或 OpenAI 额度

### 8.3 前端无法连接后端
- 确认 vercel.json 中的 API 转发配置
- 检查 Railway 服务状态

---

## 九、配置说明

### 9.1 环境变量 (.env)

| 变量 | 必需 | 描述 |
|------|------|------|
| PRIMARY_PROVIDER | 是 | AI 提供商 (openai/longcat) |
| LONGCAT_API_KEY | 否 | Longcat API Key |
| OPENAI_API_KEY | 否 | OpenAI API Key |
| JWT_SECRET | 是 | JWT 密钥 |
| DATABASE_URL | 否 | 数据库路径 |
| DEMO_MODE | 否 | 演示模式 |

### 9.2 Railway 变量
在 Railway 控制台添加同名环境变量。

---

## 十、后续开发

### 10.1 待实现功能
- [ ] 小程序适配
- [ ] 食谱分享到社交媒体
- [ ] 语音输入食材
- [ ] 菜谱分类浏览
- [ ] 用户 followers
- [ ] 推荐系统

### 10.2 性能优化
- [ ] 数据库索引优化
- [ ] API 缓存
- [ ] 图片 CDN
- [ ] 分页加载

---

*最后更新: 2026-04-25*