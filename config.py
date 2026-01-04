"""
Configuration module for Reviews Analyzer service
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Slack Configuration
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

# Notification Method
NOTIFICATION_METHOD = os.getenv("NOTIFICATION_METHOD", "telegram")

# Schedule Configuration
SCHEDULE_DAY_OF_WEEK = os.getenv("SCHEDULE_DAY_OF_WEEK", "monday")
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "09:00")

# Reviews Configuration
REVIEWS_PER_APP = int(os.getenv("REVIEWS_PER_APP", "100"))

# Git Configuration (for syncing subscribers) - DEPRECATED, using Supabase now
GIT_TOKEN = os.getenv("GIT_TOKEN")  # GitHub Personal Access Token for pushing changes

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # anon public key
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")  # Optional: direct PostgreSQL connection

# Directories
BASE_DIR = Path(__file__).parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
REVIEWS_DIR = DATA_DIR / "reviews"
OUTPUT_DIR = DATA_DIR / "outputs"
HISTORY_DIR = OUTPUT_DIR / "history"

# Reports directory (saved in repository for bot access)
REPORTS_DIR = BASE_DIR / "reports"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
REVIEWS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
HISTORY_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Competitors configuration
# This will be populated by the user
COMPETITORS = []

