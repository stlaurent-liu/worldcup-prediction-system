"""Resolve SQLite path for world-cup-prediction scripts."""
import os
import shutil

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SKILL_ROOT, "data")
DEFAULT_DB = os.path.join(DATA_DIR, "football_database.sqlite")
SAMPLE_DB = os.path.join(SKILL_ROOT, "sample_data", "football_database_sample.sqlite")


def get_db_path() -> str:
    env = os.environ.get("WC2026_DB_PATH")
    if env:
        return env
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DEFAULT_DB) and os.path.exists(SAMPLE_DB):
        shutil.copy2(SAMPLE_DB, DEFAULT_DB)
    return DEFAULT_DB