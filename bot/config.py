"""Configuration loader for the Telegram bot.

Reads secrets from .env.bot.secret in the bot directory.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


def load_config() -> dict[str, str]:
    """Load configuration from .env.bot.secret.
    
    Returns a dict with keys: BOT_TOKEN, LMS_API_URL, LMS_API_KEY,
    LLM_API_KEY, LLM_API_BASE_URL, LLM_API_MODEL
    """
    # Find the .env.bot.secret file in the bot directory
    bot_dir = Path(__file__).parent
    env_file = bot_dir / ".env.bot.secret"
    
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Try loading from parent directory (for development)
        parent_env = bot_dir.parent / ".env.bot.secret"
        if parent_env.exists():
            load_dotenv(parent_env)
    
    return {
        "BOT_TOKEN": os.getenv("BOT_TOKEN", ""),
        "LMS_API_URL": os.getenv("LMS_API_URL", "http://localhost:42002"),
        "LMS_API_KEY": os.getenv("LMS_API_KEY", "my-secret-api-key"),
        "LLM_API_KEY": os.getenv("LLM_API_KEY", ""),
        "LLM_API_BASE_URL": os.getenv("LLM_API_BASE_URL", "http://localhost:42005/v1"),
        "LLM_API_MODEL": os.getenv("LLM_API_MODEL", "coder-model"),
    }
