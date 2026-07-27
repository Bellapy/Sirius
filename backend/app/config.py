import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "app.db"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

AI_MODE = os.environ.get("AI_MODE", "simulated")
