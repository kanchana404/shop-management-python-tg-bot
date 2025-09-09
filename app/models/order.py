"""Order model and schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from .cart import CartItem


class OrderStatus(str, Enum):
    """Order status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Order(BaseModel):
    """Order model."""
    id: Optional[str] = Field(None, alias="_id")
    user_id: int = Field(..., description="User's Telegram ID")
    items: List[CartItem] = Field(..., description="Ordered items")
    total_amount: float = Field(..., description="Total order amount")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Order status")
    payment_method: str = Field(default="balance", description="Payment method used")
    notes: Optional[str] = Field(None, description="Order notes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic config."""
        populate_by_name = True
        use_enum_values = True


class OrderCreate(BaseModel):
    """Schema for creating an order."""
    user_id: int
    items: List[CartItem]
    total_amount: float
    status: OrderStatus = OrderStatus.PENDING
    payment_method: str = "balance"
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic config."""
        use_enum_values = True


class OrderUpdate(BaseModel):
    """Schema for updating an order."""
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OrderFilter(BaseModel):
    """Schema for filtering orders."""
    user_id: Optional[int] = None
    status: Optional[OrderStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
