"""Announcement model and schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class AnnouncementType(str, Enum):
    """Announcement types."""
    DAILY_MESSAGE = "daily_message"
    RESTOCK = "restock"
    NEW_PRODUCT = "new_product"
    BROADCAST = "broadcast"


class AnnouncementStatus(str, Enum):
    """Announcement status."""
    SCHEDULED = "scheduled"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Announcement(BaseModel):
    """Announcement model."""
    id: Optional[str] = Field(None, alias="_id")
    type: AnnouncementType = Field(..., description="Announcement type")
    text: str = Field(..., description="Announcement text")
    photo: Optional[str] = Field(None, description="Photo file ID or URL")
    scheduled_at: datetime = Field(..., description="When to send the announcement")
    sent_at: Optional[datetime] = Field(None, description="When announcement was sent")
    status: AnnouncementStatus = Field(default=AnnouncementStatus.SCHEDULED, description="Announcement status")
    target_group_id: Optional[int] = Field(None, description="Target group/channel ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic config."""
        populate_by_name = True
        use_enum_values = True


class AnnouncementCreate(BaseModel):
    """Schema for creating an announcement."""
    type: AnnouncementType
    text: str
    photo: Optional[str] = None
    scheduled_at: datetime
    target_group_id: Optional[int] = None


class AnnouncementUpdate(BaseModel):
    """Schema for updating an announcement."""
    text: Optional[str] = None
    photo: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    status: Optional[AnnouncementStatus] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
