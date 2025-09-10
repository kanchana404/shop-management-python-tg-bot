"""Configuration settings for the Telegram Shop Bot."""

import os
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    """Application settings."""
    
    # Bot Configuration
    bot_tokens: List[str] = Field(...)
    
    # Telegram API (these can be default for bot usage)
    api_id: int = Field(default=6)
    api_hash: str = Field(default="eb06d4abfb49dc3eeb1aeb98ae0f581e")
    
    # MongoDB Configuration
    mongo_uri: str = Field(...)
    database_name: str = Field(default="telegram_shop")
    
    # Telegram Configuration
    main_group_id: Optional[int] = Field(None)
    main_channel_id: Optional[int] = Field(None)
    
    # Admin Configuration
    owner_id: int = Field(...)
    admin_ids: List[int] = Field(default_factory=list)
    
    # Rate Limiting
    rate_limit_messages: int = Field(default=5)
    rate_limit_window: int = Field(default=60)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="bot.log")
    
    # Session Files
    session_dir: str = Field(default="sessions")
    
    # Environment
    environment: str = Field(default="development")
    
    # Admin Notifications
    admin_startup_message: Optional[str] = Field(None, description="Custom admin startup message")
    
    # Crypto Pay Configuration
    crypto_pay_token: Optional[str] = Field(None, description="Crypto Pay API token")
    crypto_pay_testnet: bool = Field(default=False, description="Use Crypto Pay testnet")
    
    @field_validator("bot_tokens", mode="before")
    @classmethod
    def parse_bot_tokens(cls, v):
        """Parse comma-separated bot tokens."""
        if isinstance(v, str):
            return [token.strip() for token in v.split(",") if token.strip()]
        return v
    
    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        """Parse comma-separated admin IDs."""
        if isinstance(v, str):
            return [int(admin_id.strip()) for admin_id in v.split(",") if admin_id.strip()]
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def all_admin_ids(self) -> List[int]:
        """Get all admin IDs including owner."""
        return [self.owner_id] + self.admin_ids
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False


# Global settings instance - manually load from environment
def _load_settings():
    """Load settings from environment variables."""
    import os
    
    # Parse bot tokens
    bot_tokens_str = os.getenv("BOT_TOKENS", "")
    bot_tokens = [token.strip() for token in bot_tokens_str.split(",") if token.strip()] if bot_tokens_str else []
    
    # Parse admin IDs
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    admin_ids = [int(admin_id.strip()) for admin_id in admin_ids_str.split(",") if admin_id.strip()] if admin_ids_str else []
    
    return Settings(
        bot_tokens=bot_tokens,
        api_id=int(os.getenv("API_ID", "6")),
        api_hash=os.getenv("API_HASH", "eb06d4abfb49dc3eeb1aeb98ae0f581e"),
        mongo_uri=os.getenv("MONGO_URI", "mongodb://localhost:27017/telegram_shop"),
        database_name=os.getenv("DATABASE_NAME", "telegram_shop"),
        main_group_id=int(os.getenv("MAIN_GROUP_ID")) if os.getenv("MAIN_GROUP_ID") else None,
        main_channel_id=int(os.getenv("MAIN_CHANNEL_ID")) if os.getenv("MAIN_CHANNEL_ID") else None,
        owner_id=int(os.getenv("OWNER_ID", "0")),
        admin_ids=admin_ids,
        rate_limit_messages=int(os.getenv("RATE_LIMIT_MESSAGES", "5")),
        rate_limit_window=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE", "bot.log"),
        session_dir=os.getenv("SESSION_DIR", "sessions"),
        environment=os.getenv("ENVIRONMENT", "development"),
        admin_startup_message=os.getenv("ADMIN_STARTUP_MESSAGE"),
        crypto_pay_token=os.getenv("CRYPTO_PAY_TOKEN"),
        crypto_pay_testnet=os.getenv("CRYPTO_PAY_TESTNET", "false").lower() == "true"
    )

settings = _load_settings()
