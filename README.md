# MealMate

**Smart recipes from your fridge** — an AI-powered recipe app with social sharing.

## Features

- **AI Recipe Generation** — enter ingredients, get 2–3 recipes instantly via OpenAI
- **Conversational AI** — chat to modify recipes ("make it vegan", "under 15 minutes")
- **Social Feed** — publish, like, comment, and bookmark recipes
- **Remix System** — fork others' recipes with your own twist
- **Smart Shopping** — affiliate links to buy missing ingredients
- **User Profiles** — dietary preferences, allergies, skill level, favorite cuisines
- **Notifications** — likes, comments, and remixes on your recipes

## Tech Stack

| Layer    | Tech                         |
|----------|------------------------------|
| Frontend | React 18 + Vite + TailwindCSS |
| Backend  | Python FastAPI               |
| Database | SQLite (SQLAlchemy)          |
| AI       | OpenAI API (gpt-4o-mini)     |
| Deploy   | Docker                       |

## Quick Start

### Option 1: Docker (Recommended)

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and JWT_SECRET

# 2. Build and run
docker-compose up --build

# 3. Open http://localhost:8000
```

### Option 2: Local Development

**Backend:**
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173 (proxies API to :8000)
```

## Environment Variables

| Variable         | Required | Description                |
|------------------|----------|----------------------------|
| `OPENAI_API_KEY` | Yes      | Your OpenAI API key        |
| `JWT_SECRET`     | Yes      | Random string for JWT auth |
| `DATABASE_URL`   | No       | SQLite path (has default)  |

## Project Structure

```
mealmate/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── config.py        # Settings
│   │   ├── database.py      # SQLAlchemy setup
│   │   ├── models.py        # DB models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── auth.py          # JWT auth
│   │   └── routers/         # API routes
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/           # React pages
│   │   ├── components/      # Reusable components
│   │   ├── context/         # Auth context
│   │   └── api.js           # Axios API client
│   └── package.json
├── Dockerfile               # Multi-stage build
├── docker-compose.yml
└── README.md
```

## API Endpoints

| Method | Path                           | Description            |
|--------|--------------------------------|------------------------|
| POST   | `/api/auth/register`           | Create account         |
| POST   | `/api/auth/login`              | Sign in                |
| GET    | `/api/auth/me`                 | Current user           |
| PUT    | `/api/users/me`                | Update profile         |
| POST   | `/api/ai/generate`             | Generate recipes       |
| POST   | `/api/ai/chat/{session_id}`    | Chat with AI           |
| GET    | `/api/recipes/feed`            | Recipe feed            |
| POST   | `/api/recipes`                 | Create recipe          |
| GET    | `/api/recipes/{id}`            | Recipe detail          |
| POST   | `/api/recipes/{id}/like`       | Toggle like            |
| POST   | `/api/recipes/{id}/comments`   | Add comment            |
| POST   | `/api/bookmarks/{id}`          | Toggle bookmark        |
| GET    | `/api/notifications`           | Get notifications      |
