"""Audit log model and schemas."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum


class AuditAction(str, Enum):
    """Audit actions."""
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_BANNED = "user_banned"
    USER_UNBANNED = "user_unbanned"
    PRODUCT_CREATED = "product_created"
    PRODUCT_UPDATED = "product_updated"
    PRODUCT_DELETED = "product_deleted"
    ORDER_CREATED = "order_created"
    ORDER_UPDATED = "order_updated"
    DEPOSIT_CREATED = "deposit_created"
    DEPOSIT_CONFIRMED = "deposit_confirmed"
    BALANCE_UPDATED = "balance_updated"
    ANNOUNCEMENT_SENT = "announcement_sent"
    ADMIN_ACTION = "admin_action"
    SETTINGS_UPDATED = "settings_updated"


class AuditLog(BaseModel):
    """Audit log model."""
    id: Optional[str] = Field(None, alias="_id")
    action: AuditAction = Field(..., description="Action performed")
    user_id: Optional[int] = Field(None, description="User who performed the action")
    target_user_id: Optional[int] = Field(None, description="Target user (if applicable)")
    target_id: Optional[str] = Field(None, description="Target object ID")
    details: Dict[str, Any] = Field(default_factory=dict, description="Action details")
    ip_address: Optional[str] = Field(None, description="IP address (if available)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic config."""
        populate_by_name = True
        use_enum_values = True


class AuditLogCreate(BaseModel):
    """Schema for creating an audit log entry."""
    action: AuditAction
    user_id: Optional[int] = None
    target_user_id: Optional[int] = None
    target_id: Optional[str] = None
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
