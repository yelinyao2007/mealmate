import os
import logging
import sqlite3
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _sqlite_url_for_path(path: str) -> str:
    return f"sqlite:///{os.path.abspath(path).replace(os.sep, '/')}"


def _sqlite_path_from_url(db_url: str) -> str:
    if db_url == "sqlite:///:memory:":
        return ":memory:"
    return db_url.replace("sqlite:///", "", 1)


def _normalize_sqlite_url(db_url: str) -> str:
    if db_url == "sqlite:///:memory:":
        return db_url

    path = _sqlite_path_from_url(db_url)
    if not os.path.isabs(path):
        # Keep relative paths stable regardless of where uvicorn is launched.
        path = os.path.join(BASE_DIR, path)
    return _sqlite_url_for_path(path)


def _validate_sqlite_url(db_url: str) -> bool:
    path = _sqlite_path_from_url(db_url)
    if path == ":memory:":
        return True

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        conn = sqlite3.connect(path)
        try:
            conn.execute("PRAGMA quick_check").fetchone()
            conn.execute("CREATE TABLE IF NOT EXISTS __db_write_test (id INTEGER PRIMARY KEY)")
            conn.execute("DROP TABLE IF EXISTS __db_write_test")
            conn.commit()
        finally:
            conn.close()
        return True
    except Exception as exc:
        logger.warning("[DATABASE] SQLite database is not usable (%s): %s", path, exc)
        return False


def _candidate_sqlite_urls() -> list[str]:
    candidates = [
        os.path.join(BASE_DIR, "data", "mealmate.db"),
    ]

    if os.name != "nt":
        candidates.extend([
            "/data/mealmate.db",
            "/tmp/data/mealmate.db",
        ])
    else:
        candidates.append(r"D:\tmp\mealmate_demo.db")

    candidates.append(os.path.join(tempfile.gettempdir(), "mealmate_demo.db"))
    return [_sqlite_url_for_path(path) for path in candidates]


def _resolve_database_url() -> str:
    env_db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")

    if env_db_url:
        if env_db_url.startswith("postgres"):
            if "railway.internal" in env_db_url:
                logger.warning("[DATABASE] Railway internal PostgreSQL detected - using SQLite fallback")
            else:
                logger.info("[DATABASE] Using PostgreSQL")
                return env_db_url
        elif env_db_url.startswith("sqlite"):
            normalized = _normalize_sqlite_url(env_db_url)
            if _validate_sqlite_url(normalized):
                logger.info("[DATABASE] Using SQLite from DATABASE_URL: %s", normalized)
                return normalized
            logger.warning("[DATABASE] DATABASE_URL SQLite target failed validation; trying fallback databases")
        else:
            logger.warning("[DATABASE] Unsupported DATABASE_URL scheme; using SQLite fallback")

    for candidate_url in _candidate_sqlite_urls():
        if _validate_sqlite_url(candidate_url):
            logger.info("[DATABASE] Using SQLite at %s", candidate_url)
            return candidate_url

    raise RuntimeError("No writable database location found")


_db_url = _resolve_database_url()

connect_args = {} if not _db_url.startswith("sqlite") else {"check_same_thread": False}

engine = create_engine(_db_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _migrate_database():
    if not _db_url.startswith("sqlite://"):
        return
    import sqlite3
    db_path = _db_url.replace("sqlite:///", "", 1)
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(recipes)")
    recipes_cols = {row[1] for row in cursor.fetchall()}

    recipes_migrations = [
        ("is_agent_generated", "ALTER TABLE recipes ADD COLUMN is_agent_generated BOOLEAN DEFAULT 0"),
        ("source_agent", "ALTER TABLE recipes ADD COLUMN source_agent VARCHAR(50) DEFAULT ''"),
        ("remix_parent_id", "ALTER TABLE recipes ADD COLUMN remix_parent_id INTEGER"),
        ("cook_time_minutes", "ALTER TABLE recipes ADD COLUMN cook_time_minutes INTEGER DEFAULT 0"),
        ("prep_time_minutes", "ALTER TABLE recipes ADD COLUMN prep_time_minutes INTEGER DEFAULT 0"),
        ("difficulty", "ALTER TABLE recipes ADD COLUMN difficulty VARCHAR(50) DEFAULT ''"),
        ("tip", "ALTER TABLE recipes ADD COLUMN tip TEXT DEFAULT ''"),
    ]

    for col_name, sql in recipes_migrations:
        if col_name not in recipes_cols:
            try:
                cursor.execute(sql)
                print(f"Migrated recipes: added {col_name}")
            except Exception as e:
                print(f"Skipping recipes.{col_name}: {e}")

    cursor.execute("PRAGMA table_info(chat_sessions)")
    chat_cols = {row[1] for row in cursor.fetchall()}

    chat_migrations = [
        ("current_recipe_id", "ALTER TABLE chat_sessions ADD COLUMN current_recipe_id INTEGER"),
        ("agent_type", "ALTER TABLE chat_sessions ADD COLUMN agent_type VARCHAR(50) DEFAULT 'agent_1'"),
        ("is_active", "ALTER TABLE chat_sessions ADD COLUMN is_active BOOLEAN DEFAULT 1"),
    ]

    for col_name, sql in chat_migrations:
        if col_name not in chat_cols:
            try:
                cursor.execute(sql)
                print(f"Migrated chat_sessions: added {col_name}")
            except Exception as e:
                print(f"Skipping chat_sessions.{col_name}: {e}")

    cursor.execute("PRAGMA table_info(comments)")
    comment_cols = {row[1] for row in cursor.fetchall()}

    if "is_ai_generated" not in comment_cols:
        try:
            cursor.execute("ALTER TABLE comments ADD COLUMN is_ai_generated BOOLEAN DEFAULT 0")
            print("Migrated comments: added is_ai_generated")
        except Exception as e:
            print(f"Skipping comments.is_ai_generated: {e}")

    cursor.execute("PRAGMA table_info(users)")
    user_cols = {row[1] for row in cursor.fetchall()}

    if "language" not in user_cols:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN language VARCHAR(10) DEFAULT 'en'")
            print("Migrated users: added language")
        except Exception as e:
            print(f"Skipping users.language: {e}")

    user_profile_migrations = [
        ("height", "ALTER TABLE users ADD COLUMN height REAL DEFAULT 0.0"),
        ("weight", "ALTER TABLE users ADD COLUMN weight REAL DEFAULT 0.0"),
        ("age", "ALTER TABLE users ADD COLUMN age INTEGER DEFAULT 0"),
        ("goal", "ALTER TABLE users ADD COLUMN goal VARCHAR(50) DEFAULT ''"),
        ("target_calories", "ALTER TABLE users ADD COLUMN target_calories INTEGER DEFAULT 0"),
        ("health_conditions", "ALTER TABLE users ADD COLUMN health_conditions JSON DEFAULT '[]'"),
    ]

    for col_name, sql in user_profile_migrations:
        if col_name not in user_cols:
            try:
                cursor.execute(sql)
                print(f"Migrated users: added {col_name}")
            except Exception as e:
                print(f"Skipping users.{col_name}: {e}")

    cursor.execute("PRAGMA table_info(saved_recipes)")
    saved_cols = {row[1] for row in cursor.fetchall()}

    saved_migrations = [
        ("source", "ALTER TABLE saved_recipes ADD COLUMN source VARCHAR(100) DEFAULT ''"),
        ("inferred_tags", "ALTER TABLE saved_recipes ADD COLUMN inferred_tags JSON DEFAULT '[]'"),
    ]

    for col_name, sql in saved_migrations:
        if col_name not in saved_cols:
            try:
                cursor.execute(sql)
                print(f"Migrated saved_recipes: added {col_name}")
            except Exception as e:
                print(f"Skipping saved_recipes.{col_name}: {e}")

    conn.commit()
    conn.close()


def get_db():
    _migrate_database()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
