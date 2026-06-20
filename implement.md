# MealMate – Implementation Guide

## 1. Project Structure

```
mealmate/
├── run.py                       # Entry point – run from project root
├── requirements.txt             # Python dependencies (root level)
├── .env.example                 # Environment variable template
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry + static file serving
│   │   ├── config.py            # Settings & env vars
│   │   ├── database.py          # SQLAlchemy setup (absolute paths)
│   │   ├── models.py            # ORM models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── auth.py              # JWT auth utilities
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── auth.py          # /auth endpoints
│   │       ├── users.py         # /users endpoints
│   │       ├── recipes.py       # /recipes endpoints
│   │       ├── ai.py            # /ai endpoints
│   │       ├── social.py        # likes, comments, follow
│   │       ├── bookmarks.py     # /bookmarks endpoints
│   │       └── notifications.py # /notifications endpoints
│   ├── static/
│   │   └── index.html           # No-build HTML frontend (Tailwind CDN + vanilla JS)
│   ├── data/
│   │   └── mealmate.db          # SQLite database (auto-created)
│   └── requirements.txt         # (mirror of root, for Docker)
├── frontend/                    # React SPA (requires Node.js, used in Docker build)
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── api.js               # Axios instance + API helpers
│       ├── context/
│       │   └── AuthContext.jsx
│       ├── pages/               # 10 page components
│       └── components/          # 5 shared components
├── Dockerfile                   # Multi-stage: Node build → Python runtime
├── docker-compose.yml
├── plan.md
├── implement.md
├── happy_path.md                # Manual testing guide (9 flows)
└── README.md
```

## 2. Backend Implementation

### 2.1 Database (SQLAlchemy + SQLite)
- SQLAlchemy 2.0 (sync mode, `check_same_thread=False` for SQLite)
- SQLite file stored at `backend/data/mealmate.db` (uses absolute path resolution)
- Volume-mounted at `/app/data` in Docker for persistence
- JSON columns for `preferences`, `ingredients`, `steps`, `messages`

### 2.2 Authentication
- Password hashing: `passlib[bcrypt]`
- JWT tokens: `python-jose[cryptography]`
- Token expiry: 7 days
- Middleware extracts current user from `Authorization: Bearer <token>`

### 2.3 AI Integration (OpenAI)
- **POST /ai/generate**: accepts `{ ingredients: string[], preferences: {} }`
  - System prompt includes user dietary preferences
  - Returns 2–3 structured recipes as JSON
- **POST /ai/chat/{session_id}**: accepts `{ message: string }`
  - Appends to conversation history stored in ChatSession
  - AI responds with modified recipe or clarification
- Model: `gpt-4o-mini` (cost-effective) or `gpt-4o` for vision
- Structured output via JSON mode

### 2.4 Key Business Logic
- **Remix**: creating a recipe with `remix_parent_id` set → triggers notification to original author
- **Like toggle**: single endpoint flips like on/off
- **Feed**: paginated, filterable by followed-users-only or global
- **Savings report**: sum estimated cost of ingredients used across recipes in the past 7 days

## 3. Frontend Implementation

Two frontends are provided:

- **Static HTML** (`backend/static/index.html`) — zero build step, works with Python only.
  Uses Tailwind CDN, vanilla JS, hash-based navigation. Full feature coverage.
- **React SPA** (`frontend/`) — requires Node.js. Built via Vite, uses React Router,
  Axios, Lucide icons. Used in Docker production builds.

### 3.1 Routing (React Router v6 / hash-based in static)
| Path                  | Page             | Auth Required |
|-----------------------|------------------|---------------|
| `/`                   | Landing          | No            |
| `/login`              | Login            | No            |
| `/register`           | Register         | No            |
| `/profile`            | Profile          | Yes           |
| `/ai`                 | AIChef           | Yes           |
| `/feed`               | RecipeFeed       | No            |
| `/recipes/:id`        | RecipeDetail     | No            |
| `/recipes/new`        | CreateRecipe     | Yes           |
| `/bookmarks`          | Bookmarks        | Yes           |
| `/notifications`      | Notifications    | Yes           |

### 3.2 State Management
- `AuthContext` for user session (token in localStorage)
- Local state per page (no Redux needed at this scale)

### 3.3 Design Tokens
```css
--color-cream:      #FFF8F0;
--color-terracotta: #E07A5F;
--color-sage:       #81B29A;
--color-charcoal:   #3D405B;
--color-gold:       #F2CC8F;
--font-heading:     'Patrick Hand', cursive;
--font-body:        'Inter', sans-serif;
```

### 3.4 Key UI Patterns
- **Mobile-first**: max-width 480px default, responsive breakpoints at sm/md/lg
- **Recipe cards**: rounded corners, soft shadow, ingredient pills
- **AI chat**: message bubbles with typing indicator
- **Ingredient input**: tag-style chips with autocomplete

## 4. Docker Setup

### Dockerfile (multi-stage)
1. **Stage 1 – Frontend build**: Node 20, `npm install && npm run build`
2. **Stage 2 – Production**: Python 3.12-slim, copy backend + built frontend
3. FastAPI serves React static files at `/` and API at `/api`

### docker-compose.yml
- Single service for simplicity
- Volume mount for SQLite data persistence
- Environment variables: `OPENAI_API_KEY`, `JWT_SECRET`

## 5. Environment Variables

| Variable         | Description                     | Default          |
|------------------|---------------------------------|------------------|
| `OPENAI_API_KEY` | OpenAI API key                  | (required)       |
| `JWT_SECRET`     | Secret for signing JWT tokens   | (required)       |
| `DATABASE_URL`   | SQLite path                     | `sqlite:///./data/mealmate.db` |

## 6. Running Locally

```powershell
# Install deps into the venv
.venv\Scripts\pip.exe install -r requirements.txt

# (Optional) Set your OpenAI API key
copy .env.example .env
# Edit .env → set OPENAI_API_KEY=sk-...

# Start the server
.venv\Scripts\python.exe run.py
# → http://127.0.0.1:8000
```

`run.py` adds `backend/` to `sys.path` so `app.main` can be imported
from the project root. Uvicorn watches `backend/` for hot-reload.

## 7. Implementation Order (completed)

1. ✅ Backend: `config.py` → `database.py` → `models.py` → `schemas.py` → `auth.py`
2. ✅ Backend routers: `auth.py` → `users.py` → `recipes.py` → `ai.py` → `social.py` → `bookmarks.py` → `notifications.py`
3. ✅ Backend: `main.py` (wire everything, static file serving)
4. ✅ Static HTML frontend: `backend/static/index.html`
5. ✅ React frontend: `frontend/` (requires Node.js)
6. ✅ Docker: `Dockerfile` → `docker-compose.yml` → `README.md`
7. ✅ Testing guide: `happy_path.md`
