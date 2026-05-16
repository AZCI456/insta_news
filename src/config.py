"""
Centralized configuration for insta_news.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

BASE_DIR = _PROJECT_ROOT
# Default is off-repo so a fresh clone never writes subscriber data under the app tree.
_DATA_ROOT_DEFAULT = "/opt/insta_news_data"
DATA_ROOT = Path(os.getenv("insta_news_data_root", _DATA_ROOT_DEFAULT)).expanduser()
DB_PATH = Path(os.getenv("insta_news_db_path", DATA_ROOT / "insta_news.db"))


DATA_ROOT.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

INSTAGRAM_USERNAME = os.getenv("insta_username", "")
GEMINI_API_KEY = os.getenv("genai_api_key", "")
FERNET_EMAIL_ENC_KEY = os.getenv("FERNET_EMAIL_ENC_KEY", "")

DB_CONFIG = {"path": str(DB_PATH), "timeout": 30}

TEMPLATES_DIR = BASE_DIR / "src" / "web" / "templates"
STATIC_DIR = BASE_DIR / "src" / "web" / "static"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
