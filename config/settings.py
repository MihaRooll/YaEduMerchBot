"""Configuration settings for the bot."""

import os
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Bot configuration settings."""
    
    # Telegram Bot Configuration
    BOT_TOKEN: str = Field(default="", description="Telegram bot token")
    
    # Database Configuration
    DATABASE_URL: str = Field(default="sqlite:///bot.db", description="Database connection URL")
    
    # Admin Configuration
    ADMIN_IDS: str = Field(default="", description="Comma-separated admin IDs")
    
    # Payment Configuration
    PAYMENT_TOKEN: str = Field(default="", description="Payment provider token")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # Other Configuration
    DEBUG: bool = Field(default=False, description="Debug mode")
    WEBHOOK_URL: str = Field(default="", description="Webhook URL")
    WEBHOOK_PORT: int = Field(default=8443, description="Webhook port")
    
    @field_validator('DEBUG', mode='before')
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    
    def get_admin_ids(self) -> List[int]:
        """Parse ADMIN_IDS string into list of integers."""
        if not self.ADMIN_IDS:
            return []
        try:
            return [int(id_.strip()) for id_ in self.ADMIN_IDS.split(",") if id_.strip()]
        except ValueError:
            return []
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
