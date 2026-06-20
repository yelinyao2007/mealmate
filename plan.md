# MealMate – Project Plan

## 1. Vision
A full-stack web app that helps users reduce food waste by generating AI-powered recipes from ingredients they already have, with a social layer for sharing and remixing recipes.

## 2. Tech Stack

| Layer            | Technology                                           |
|------------------|------------------------------------------------------|
| Frontend (dev)   | Single-file HTML + Tailwind CDN + vanilla JS (no Node required) |
| Frontend (prod)  | React 18 + Vite + TailwindCSS (built via Docker)    |
| UI Library       | Lucide icons (React), emoji icons (static HTML)      |
| Backend          | Python FastAPI                                       |
| Database         | SQLite (via SQLAlchemy)                              |
| AI               | OpenAI API (gpt-4o-mini / gpt-4o)                   |
| Auth             | JWT-based (email/password)                           |
| Deployment       | Docker + docker-compose                              |

> **Local dev requires only Python.** Node.js is optional (only needed if
> you want to develop the React frontend). The static HTML frontend at
> `backend/static/index.html` provides full functionality without a build step.

## 3. Feature Modules

### 3.1 Onboarding & User Profile
- Email sign-up / login with JWT tokens
- Profile page: food preferences (vegetarian, low-carb, allergies), cooking skill level, favorite cuisines
- Edit profile

### 3.2 AI Recipe Agent (Core)
- **Text input**: user types a comma-separated list of ingredients
- **Photo input** (stretch): upload fridge/pantry photo → OpenAI Vision extracts ingredients
- AI generates 2–3 recipes prioritized by "use soonest expiry"
- **Conversational adjustment**: chat with AI to modify recipes ("remove spicy", "make it under 20 min", "replace chicken with tofu")
- Each chat is stored as a `ChatSession`

### 3.3 Recipe Sharing & Community
- Publish recipes (title, ingredients, steps, photos)
- Feed: scrollable list sorted by newest / most liked
- Like, comment, bookmark recipes
- **Remix**: fork someone's recipe, add a twist, publish as variation linked to original

### 3.4 Consumer / Monetization Hooks
- "Buy missing ingredients" button per recipe → affiliate links (Qianwen / Yuanbao)
- Smart cookware / seasoning recommendations (affiliate)
- Weekly savings report: estimate money saved by using leftovers

### 3.5 Notifications & Engagement
- In-app notifications: likes, comments, remixes on your recipes
- (Optional) Weekly trending digest

## 4. Database Schema

```
User
  id, email, password_hash, name, avatar_url,
  preferences (JSON: dietary, skill_level, cuisines, allergies),
  created_at

Recipe
  id, title, description, ingredients (JSON), steps (JSON),
  image_url, author_id (FK→User), likes_count,
  remix_parent_id (FK→Recipe, nullable),
  created_at

Comment
  id, text, author_id (FK→User), recipe_id (FK→Recipe), created_at

ChatSession
  id, user_id (FK→User), messages (JSON), created_at

SavedRecipe
  id, user_id (FK→User), recipe_id (FK→Recipe), created_at

Notification
  id, user_id (FK→User), type, message, recipe_id, is_read, created_at

Follow
  id, follower_id (FK→User), following_id (FK→User), created_at
```

## 5. API Endpoints (Summary)

| Group       | Endpoints                                          |
|-------------|----------------------------------------------------|
| Auth        | POST /auth/register, POST /auth/login, GET /auth/me |
| Profile     | GET/PUT /users/{id}, PUT /users/me/preferences     |
| AI          | POST /ai/generate, POST /ai/chat/{session_id}      |
| Recipes     | CRUD /recipes, GET /recipes/feed                   |
| Social      | POST /recipes/{id}/like, POST /recipes/{id}/comment, POST /recipes/{id}/remix |
| Bookmarks   | POST/DELETE /bookmarks/{recipe_id}, GET /bookmarks  |
| Notifications | GET /notifications, PUT /notifications/{id}/read  |
| Follow      | POST/DELETE /follow/{user_id}, GET /followers, GET /following |

## 6. Milestones

| #  | Milestone             | Scope                                          | Status |
|----|-----------------------|------------------------------------------------|--------|
| M1 | Backend foundation    | Auth, User, Recipe CRUD, DB models             | ✅ Done |
| M2 | AI integration        | Ingredient→recipe generation, chat sessions    | ✅ Done |
| M3 | Social features       | Feed, likes, comments, remix, follow, bookmarks| ✅ Done |
| M4 | Static HTML frontend  | All pages, no-build-step, Tailwind CDN         | ✅ Done |
| M5 | React frontend        | Full SPA with Vite build (requires Node.js)    | ✅ Done |
| M6 | Monetization hooks    | Affiliate links (千问 / 元宝)     | ✅ Done |
| M7 | Docker & deployment   | Dockerfile, docker-compose, production config  | ✅ Done |

## 7. How to Run

```powershell
# 1. Install dependencies (once)
.venv\Scripts\pip.exe install -r requirements.txt

# 2. (Optional) Create .env with your OpenAI key
cp .env.example .env

# 3. Start the server
.venv\Scripts\python.exe run.py
# → Open http://127.0.0.1:8000
```

## 8. Design Direction
- **Warm, hand-drawn, mobile-first** aesthetic (friendly cooking notebook feel)
- Soft earthy tones: warm cream (#FFF8F0), terracotta (#E07A5F), sage green (#81B29A)
- Rounded cards, playful typography, subtle paper texture
