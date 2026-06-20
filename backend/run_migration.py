import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alembic.config import Config
from alembic import command

alembic_cfg = Config()
alembic_cfg.set_main_option("script_location", "migrations")
alembic_cfg.set_main_option("sqlalchemy.url", "sqlite:///data/mealmate.db")

try:
    command.upgrade(alembic_cfg, "head")
    print("Migration applied successfully")
except Exception as e:
    print("Migration failed:", e)
