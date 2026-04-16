import os
from dotenv import load_dotenv

load_dotenv()

# Database - Use SQLite for local development
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    DATABASE_PATH = os.getenv("DATABASE_PATH", "./soulmate.db")
    DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://soulmate:soulmate123@localhost:5432/soulmate")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# MiniMax API (optional - for summarization and embeddings)
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_GROUP_ID = os.getenv("MINIMAX_GROUP_ID")
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-Text-01")
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"

# EvoMap
EVOMAP_BASE_URL = "https://evomap.ai"
EVOMAP_NODE_ID = os.getenv("EVOMAP_NODE_ID")
EVOMAP_NODE_SECRET = os.getenv("EVOMAP_NODE_SECRET")

# Memory settings
SHORT_TERM_MAX_MESSAGES = 100
SHORT_TERM_TTL_SECONDS = 86400  # 24 hours
RECENT_MEMORY_DAYS = 3
SOUL_MEMORY_IMPORTANCE_THRESHOLD = 0.7
FORGETTING_STRENGTH_THRESHOLD = 0.3
