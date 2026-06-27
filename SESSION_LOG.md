# MealMate Development Session Log

> Date: 2026-06-26  
> LLM Provider: StepFun MiMo (mimo-v2.5-pro)  
> Branch: `dev`  
> Repo: `github.com/yujun2006/mealmate`

---

## 1. Project Bootstrap & First Run

**Goal:** Analyze the project and get it running.

**Actions:**
- Created `backend/.env` with `DEMO_MODE=true` (no API key needed initially)
- Created Python venv: `backend/venv/`
- Installed backend deps: `pip install -r requirements.txt`
- Installed frontend deps: `npm install` (fixed vite execute permission)
- Started backend: `uvicorn app.main:app --host 127.0.0.1 --port 8000` (from `backend/` dir)
- Started frontend: `npm run dev` on port 5173

**Project Structure:**
- **Backend:** Python FastAPI + SQLite (SQLAlchemy)
- **Frontend:** React 18 + Vite + TailwindCSS
- **AI:** Multi-provider LLM (OpenAI/Moonshot/Anthropic/Gemini/LongCat/StepFun)

---

## 2. Scenario 1: Health Profile + ProfileAgent

### 2.1 User Model Extension

Added fields to `User` model (`backend/app/models.py`):
```python
height = Column(Float, default=0.0)                     # cm
weight = Column(Float, default=0.0)                     # kg
age = Column(Integer, default=0)
goal = Column(String(50), default="")                   # lose_fat / gain_muscle / sugar_control / general
target_calories = Column(Integer, default=0)
health_conditions = Column(JSON, default=list)          # ["diabetes", "hypertension"]
```

### 2.2 New Schemas (`backend/app/schemas.py`)

- `UserProfile` — height, weight, age, goal, target_calories, health_conditions
- `UserUpdate` now accepts optional `profile: UserProfile`

### 2.3 ProfileAgent (`backend/app/agents/profile.py`)

Analyzes user profile → LLM returns:
```json
{
  "bmi": 25.95,
  "bmi_category": "超重",
  "recommended_calories": 1800,
  "macro_targets": {"protein_g": 135, "fat_g": 50, "carbs_g": 180, "fiber_g": 30},
  "goal_analysis": { ... },
  "health_warnings": ["高血压患者必须严格控制钠盐", ...],
  "weekly_core_principles": [...],
  "summary": "..."
}
```

### 2.4 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| PUT | `/api/users/me` | Update profile (new: `profile` field) |
| POST | `/api/users/me/analyze-profile` | Run ProfileAgent |

### 2.5 Database Migration

`_migrate_database()` in `database.py` auto-adds new columns to existing DB.

### 2.6 Frontend (`Profile.jsx`)

Added "Health Profile" section:
- Height (cm), Weight (kg), Age
- Goal selector: Lose Fat / Gain Muscle / Sugar Control / General
- Target Daily Calories
- Health Conditions: Diabetes, Hypertension
- "Analyze My Profile" button → calls ProfileAgent → shows results

---

## 3. Production Deployment via Nginx

**Config:** `/etc/nginx/sites-available/mealmate`

```nginx
server {
    listen 80;
    server_name 36.231.114.172;

    location / {
        root /home/qiu/workspace/succ/mealmate/backend/static;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

**Architecture:**
```
Browser → Nginx (:80)
           ├── /        → Static files (backend/static/)
           └── /api/*   → Proxy to uvicorn (:8000)
```

**Production steps:**
1. `cd frontend && npm run build`
2. `cp -r frontend/dist backend/static`
3. `nginx -t && nginx -s reload`

---

## 4. LLM Timeout Fix

**Problem:** AI Chef recipe generation failed with "LLM request timed out after 30s"

**Root cause:** StepFun MiMo API takes 30-35s to generate recipes, exceeding default 30s timeout.

**Fix:** `backend/app/llm_client.py`:
- `chat_completion` timeout: 30s → **120s**
- `chat_completion_json` timeout: 30s → **120s**
- Added `STEPFUN_TIMEOUT=120` to `.env`

---

## 5. Database Read-Only Issue (Recurring)

**Problem:** `sqlite3.OperationalError: attempt to write a readonly database`

**Root cause:** `git checkout -- backend/data/mealmate.db` restores a tracked DB file from git, which conflicts with the running backend's open file descriptor (stale journal/WAL files).

**Fix:**
```bash
rm -f backend/data/mealmate.db-journal backend/data/mealmate.db-wal backend/data/mealmate.db-shm
chmod 644 backend/data/mealmate.db
chmod 755 backend/data/
```
Then restart backend.

**Permanent fix:** Removed `backend/data/mealmate.db` from git tracking:
```bash
git rm --cached backend/data/mealmate.db
```

---

## 6. Workflow Pipeline: User Profile Integration

**Problem:** Smart Meal Workflow agents (MenuPlanner, Procurement, Nutrition, MealCustomizer) were completely disconnected from user profile data.

### 6.1 Router Injection (`workflow.py`)

When a user is authenticated, injects their profile into `input_data`:
```python
if current_user:
    input_data["user_profile"] = {
        "height": current_user.height, "weight": current_user.weight,
        "age": current_user.age, "goal": current_user.goal,
        "target_calories": current_user.target_calories,
        "health_conditions": current_user.health_conditions,
        "allergies": current_user.preferences.get("allergies", []),
        "dietary": current_user.preferences.get("dietary", []),
    }
```

### 6.2 Orchestrator (`orchestrator.py`)

All 4 workflow types pass `user_profile` to downstream agents.

### 6.3 Agents Enhanced

| Agent | What it now considers |
|-------|----------------------|
| **MenuPlanner** | Goal (high-protein for gain_muscle, low-GI for sugar_control), allergy blacklist, disease restrictions |
| **Procurement** | Excludes allergens (e.g., peanuts, shellfish), adjusts quantities by goal (+20% protein for bulking), disease-restricted foods (low-sodium for hypertension, low-GI for diabetes) |
| **NutritionAnalyzer** | Personalized score against user BMI/goal, flags risky dishes for diseases |
| **MealCustomizer** | Disease-based customizations (diabetic → low-GI, hypertension → low-sodium), allergy exclusions |

### 6.4 Verified Output

For user: `goal=gain_muscle, allergies=[Peanuts,Shellfish], hc=[hypertension]`
- **Menu:** "针对增肌目标：每餐确保高蛋白组合...严格避免过敏源..."
- **Procurement:** 蛋白食材 +15-20%, excluded: 花生(过敏红线), 腌制食品(高钠禁忌), 5 safety warnings

---

## 7. SmartChef — Natural Language Multi-Agent Cooking

### 7.1 Backend: SmartChefAgent (`agents/smart_chef.py`)

Orchestrates:
1. Parse natural language input → extract intent, mood, ingredients
2. Lock profile constraints (BMI, calorie budget, disease alerts)
3. Generate personalized recipe (profile-aware + mood + available ingredients)

### 7.2 API: `POST /api/smart-chef/generate`

Request:
```json
{"user_input": "我控糖减脂，今天加班很累想吃点热乎的，冰箱里只有西红柿和鸡蛋"}
```

Response:
```json
{
  "user_intent": {"goal": "控糖减脂", "mood": "加班疲惫", "ingredients": ["番茄","鸡蛋"]},
  "profile_check": {"bmi": 25.5, "calorie_budget_per_meal": 533, ...},
  "recipe": {"title": "暖心番茄鸡蛋汤", "calories_estimate": 280, ...},
  "chef_chat": "加班辛苦了！这碗汤快手又低脂，暖暖的喝下去...",
  "health_notes": "本餐热量在控糖减脂预算内..."
}
```

### 7.3 Frontend: SmartCook.jsx

- Chat-like natural language textarea with example hints
- Agent visualization (ProfileAgent → NutritionAnalyzer → SmartChefAgent)
- Result display: intent tags, profile check badge, recipe card with nutrition grid
- Route: `/smart-cook` (ProtectedRoute)

### 7.4 Routing Changes

- Landing page "Start Cooking" → `/smart-cook`
- Navbar: new "SmartCook" link (alongside existing "AI Chef")
- AI Chef `/ai` still accessible as before

---

## 8. Key Commands Reference

```bash
# Start backend
cd backend && nohup venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &>/tmp/mealmate-bk.log & disown

# Start frontend dev (only for frontend development, not needed with nginx)
cd frontend && npm run dev

# Build frontend for production
cd frontend && chmod +x node_modules/.bin/vite && npm run build

# Copy build to backend/static
rm -rf backend/static && cp -r frontend/dist backend/static

# Reload nginx
sudo nginx -s reload

# Check backend status
curl http://127.0.0.1:8000/docs

# Check frontend
curl http://127.0.0.1/

# Fix database readonly issue
rm -f backend/data/mealmate.db-journal backend/data/mealmate.db-wal backend/data/mealmate.db-shm
chmod 644 backend/data/mealmate.db && chmod 755 backend/data/
```

---

## 9. Files Modified/Created

| File | Change |
|------|--------|
| `backend/app/models.py` | Added 6 health profile columns to User |
| `backend/app/schemas.py` | Added UserProfile schema |
| `backend/app/routers/users.py` | Profile update + /analyze-profile endpoint |
| `backend/app/routers/auth.py` | Handle profile fields in register/update |
| `backend/app/routers/workflow.py` | Inject user_profile into input_data |
| `backend/app/routers/smart_chef.py` | **NEW** SmartChef endpoint |
| `backend/app/main.py` | Register smart_chef router |
| `backend/app/agents/profile.py` | **NEW** ProfileAgent |
| `backend/app/agents/smart_chef.py` | **NEW** SmartChefAgent |
| `backend/app/agents/menu_planner.py` | Profile-aware menu generation |
| `backend/app/agents/procurement.py` | Profile-aware procurement (allergens, goal, disease) |
| `backend/app/agents/nutrition_analyzer.py` | Profile-aware nutrition analysis |
| `backend/app/agents/meal_customizer.py` | Profile-aware meal customization |
| `backend/app/agents/orchestrator.py` | Route user_profile to all agents |
| `backend/app/database.py` | Migration for new user columns |
| `backend/app/demo_data.py` | Demo support for ProfileAgent + SmartChefAgent |
| `backend/app/llm_client.py` | Timeout 30s → 120s |
| `.gitignore` | **NEW** exclude venv/node_modules/.env/*.db |
| `frontend/src/pages/Profile.jsx` | Health profile section |
| `frontend/src/pages/SmartCook.jsx` | **NEW** Smart cooking page |
| `frontend/src/pages/Landing.jsx` | "Start Cooking" → /smart-cook |
| `frontend/src/App.jsx` | Add /smart-cook route |
| `frontend/src/components/Navbar.jsx` | Add SmartCook nav link |
| `frontend/src/i18n/en.js` | Health profile + SmartCook translations |
| `frontend/src/i18n/zh.js` | Health profile + SmartCook translations |
| `backend/.env` | StepFun MiMo configuration |

---

## 10. Git Log (dev branch)

```
12fed8b feat: add SmartChef — natural language → multi-agent cooking
84aa8ff fix: untrack mealmate.db to prevent readonly after git checkout
d330bde feat: integrate user profile into Smart Meal Workflow pipeline
6358ce8 fix: increase LLM client timeout from 30s to 120s for MiMo API
b154799 feat: add health profile fields and ProfileAgent for scenario 1
```

---

## 11. Environment Variables (`backend/.env`)

```
DEMO_MODE=false
DATABASE_URL=sqlite:///./data/mealmate.db
JWT_SECRET=change-me-to-a-random-string
PRIMARY_PROVIDER=stepfun
STEPFUN_API_KEY=sk-***
STEPFUN_BASE_URL=https://api.xiaomimimo.com/v1
STEPFUN_MODEL=mimo-v2.5-pro
STEPFUN_VISION_MODEL=mimo-v2.5
STEPFUN_TIMEOUT=120
```

---

## 12. Agent Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│  Landing → SmartCook → AIChef → Workflow → Profile          │
└──────────────────────────┬──────────────────────────────────┘
                           │ /api/*
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Nginx :80 (static + proxy)               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI :8000 (uvicorn)                      │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ SmartChef    │  │ AI Chef      │  │ Smart Meal        │  │
│  │ → parse NL   │  │ → chat       │  │ Workflow           │  │
│  │ → Profile    │  │ → generate   │  │ → MenuPlanner     │  │
│  │ → Recipe     │  │              │  │ → Procurement     │  │
│  └─────────────┘  └──────────────┘  │ → Nutrition       │  │
│                                      │ → MealCustomizer  │  │
│  ┌─────────────┐                     └───────────────────┘  │
│  │ ProfileAgent │                                           │
│  │ → BMI/Goal   │    All agents now receive user_profile:   │
│  │ → Cal/Macros │    height, weight, age, goal, calories,   │
│  └─────────────┘    health_conditions, allergies, dietary   │
└─────────────────────────────────────────────────────────────┘
```
