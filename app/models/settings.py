"""Settings model and schemas."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class BotSettings(BaseModel):
    """Bot settings model."""
    id: Optional[str] = Field(None, alias="_id")
    key: str = Field(..., description="Setting key")
    value: Any = Field(..., description="Setting value")
    description: Optional[str] = Field(None, description="Setting description")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic config."""
        populate_by_name = True


class SettingsUpdate(BaseModel):
    """Schema for updating settings."""
    value: Any
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Default settings
DEFAULT_SETTINGS = {
    "support_handle": "@grofshop",
    "daily_message_text": "🛍️ Check out our daily deals! Use /start to browse products.",
    "daily_message_enabled": True,
    "daily_message_time": "09:00",
    "welcome_message": "Welcome to our shop! 🛍️",
    "order_confirmation_message": "Thank you for your order! 📦",
    "payment_instructions": "Please follow the payment instructions below:",
    "max_cart_items": 50,
    "max_order_amount": 10000.0,
    "min_deposit_amount": 10.0,
    "max_deposit_amount": 50000.0,
    "deposit_timeout_hours": 24,
}
