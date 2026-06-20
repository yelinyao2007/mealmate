from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os
from pathlib import Path
import traceback

# Load .env file from backend directory
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

from app.database import engine, Base, _db_url
from app.routers import auth, users, recipes, ai, social, bookmarks, notifications, workflow, agent1, agent2, agent3, i18n, image_recognition

# Log which database is being used
print(f"[INFO] Using database: {_db_url[:50]}...")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MealMate API", version="1.0.0", debug=True)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(f"[ERROR] {request.method} {request.url.path}: {type(exc).__name__}: {exc}")
    print(tb)
    return JSONResponse(status_code=500, content={"detail": str(exc), "type": type(exc).__name__})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(recipes.router)
app.include_router(ai.router)
app.include_router(social.router)
app.include_router(bookmarks.router)
app.include_router(notifications.router)
app.include_router(workflow.router)
app.include_router(agent1.router)
app.include_router(agent2.router)
app.include_router(agent3.router)
app.include_router(i18n.router)
app.include_router(image_recognition.router)

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
static_dir = os.path.normpath(static_dir)

if os.path.isdir(static_dir):
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(static_dir, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            return JSONResponse({"detail": "API endpoint not found"}, status_code=404)
        file_path = os.path.join(static_dir, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))
