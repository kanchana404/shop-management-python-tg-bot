"""User model and schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class UserRole(str, Enum):
    """User roles."""
    OWNER = "owner"
    ADMIN = "admin"
    STAFF = "staff"
    USER = "user"


class LanguageCode(str, Enum):
    """Supported languages."""
    ENGLISH = "en"
    SERBIAN = "sr"
    RUSSIAN = "ru"


class User(BaseModel):
    """User model."""
    id: Optional[str] = Field(None, alias="_id")
    tg_id: int = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    balance: float = Field(default=0.0, description="User balance in EUR")
    language_code: LanguageCode = Field(default=LanguageCode.ENGLISH, description="User's language")
    roles: List[UserRole] = Field(default_factory=lambda: [UserRole.USER], description="User roles")
    is_banned: bool = Field(default=False, description="Whether user is banned")
    ban_reason: Optional[str] = Field(None, description="Reason for ban")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    reminder_sent: bool = Field(default=False)  # Track if inactivity reminder was sent
    
    class Config:
        """Pydantic config."""
        populate_by_name = True
        use_enum_values = True


class UserCreate(BaseModel):
    """Schema for creating a user."""
    tg_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: LanguageCode = LanguageCode.ENGLISH


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    balance: Optional[float] = None
    language_code: Optional[LanguageCode] = None
    roles: Optional[List[UserRole]] = None
    is_banned: Optional[bool] = None
    ban_reason: Optional[str] = None
    reminder_sent: Optional[bool] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
