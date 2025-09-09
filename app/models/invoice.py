"""Invoice model for tracking crypto payments."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from enum import Enum


class InvoiceStatus(str, Enum):
    """Invoice status enumeration."""
    PENDING = "pending"
    PAID = "paid"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class InvoiceType(str, Enum):
    """Invoice type enumeration."""
    DEPOSIT = "deposit"
    ORDER = "order"


class Invoice(BaseModel):
    """Invoice model for crypto payments."""
    
    id: Optional[str] = Field(default=None, alias="_id")
    invoice_id: int = Field(..., description="Crypto Pay invoice ID")
    user_id: int = Field(..., description="Telegram user ID")
    
    # Invoice details
    type: InvoiceType = Field(..., description="Invoice type")
    status: InvoiceStatus = Field(default=InvoiceStatus.PENDING, description="Invoice status")
    
    # Payment amounts
    amount: str = Field(..., description="Original invoice amount")
    asset: str = Field(..., description="Original asset")
    currency_type: str = Field(default="crypto", description="Currency type")
    
    # Received amounts (filled when paid)
    paid_amount: Optional[str] = Field(default=None, description="Actually received amount")
    paid_asset: Optional[str] = Field(default=None, description="Actually received asset")
    
    # Rates and fees
    paid_usd_rate: Optional[str] = Field(default=None, description="USD rate when paid")
    fee_amount: Optional[float] = Field(default=None, description="Fee amount")
    fee_asset: Optional[str] = Field(default=None, description="Fee asset")
    
    # Swap information
    is_swapped: bool = Field(default=False, description="Whether payment was swapped")
    swapped_to: Optional[str] = Field(default=None, description="Swapped to asset")
    swapped_amount: Optional[str] = Field(default=None, description="Swapped amount")
    swapped_rate: Optional[str] = Field(default=None, description="Swap rate")
    
    # Links and metadata
    bot_invoice_url: Optional[str] = Field(default=None, description="Payment URL")
    mini_app_invoice_url: Optional[str] = Field(default=None, description="Mini app URL")
    description: Optional[str] = Field(default=None, description="Invoice description")
    
    # Related data
    order_id: Optional[str] = Field(default=None, description="Related order ID")
    payload_data: Optional[Dict[str, Any]] = Field(default=None, description="Custom payload")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None, description="Expiration time")
    paid_at: Optional[datetime] = Field(default=None, description="Payment time")
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True


class InvoiceCreate(BaseModel):
    """Invoice creation model."""
    
    invoice_id: int
    user_id: int
    type: InvoiceType
    amount: str
    asset: str
    currency_type: str = "crypto"
    bot_invoice_url: Optional[str] = None
    mini_app_invoice_url: Optional[str] = None
    description: Optional[str] = None
    order_id: Optional[str] = None
    payload_data: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class InvoiceUpdate(BaseModel):
    """Invoice update model."""
    
    status: Optional[InvoiceStatus] = None
    paid_amount: Optional[str] = None
    paid_asset: Optional[str] = None
    paid_usd_rate: Optional[str] = None
    fee_amount: Optional[float] = None
    fee_asset: Optional[str] = None
    is_swapped: Optional[bool] = None
    swapped_to: Optional[str] = None
    swapped_amount: Optional[str] = None
    swapped_rate: Optional[str] = None
    paid_at: Optional[datetime] = None

    class Config:
        use_enum_values = True
