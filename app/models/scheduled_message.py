"""Scheduled message model."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId


class ScheduledMessage(BaseModel):
    """Scheduled message model."""
    
    id: Optional[str] = Field(default=None, alias="_id")
    message: str = Field(description="Message content")
    scheduled_time: datetime = Field(description="When to send the message")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: int = Field(description="Admin user ID who created this")
    is_sent: bool = Field(default=False)
    sent_at: Optional[datetime] = Field(default=None)
    recipients_count: int = Field(default=0, description="Number of users who received the message")
    errors_count: int = Field(default=0, description="Number of failed deliveries")
    target_users: Optional[List[int]] = Field(default=None, description="Specific user IDs to send to, if None send to all")
    is_active: bool = Field(default=True, description="Whether this scheduled message is active")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ScheduledMessageCreate(BaseModel):
    """Data for creating a scheduled message."""
    
    message: str
    scheduled_time: datetime
    created_by: int
    target_users: Optional[List[int]] = None


class ScheduledMessageUpdate(BaseModel):
    """Data for updating a scheduled message."""
    
    message: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    is_active: Optional[bool] = None
    target_users: Optional[List[int]] = None

