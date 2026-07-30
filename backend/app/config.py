import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

VENDOR_DIR = BASE_DIR.parent / "vendor" / "developer-roadmap"
ROADMAPS_DIR = VENDOR_DIR / "src" / "data" / "roadmaps"

DB_PATH = DATA_DIR / "app.db"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

AI_MODE = os.environ.get("AI_MODE", "simulated")

EMBEDDING_MODE = os.environ.get("EMBEDDING_MODE", "local")
EMBEDDING_MODEL_NAME = os.environ.get("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
