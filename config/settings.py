"""Configuration settings for the bot."""

import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Bot configuration settings."""
    
    # Telegram Bot Configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///bot.db")
    
    # Admin Configuration
    ADMIN_IDS: List[int] = []
    
    # Payment Configuration
    PAYMENT_TOKEN: str = os.getenv("PAYMENT_TOKEN", "")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Other Configuration
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", "8443"))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse ADMIN_IDS from comma-separated string
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        if admin_ids_str:
            try:
                self.ADMIN_IDS = [int(id_.strip()) for id_ in admin_ids_str.split(",") if id_.strip()]
            except ValueError:
                self.ADMIN_IDS = []
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
