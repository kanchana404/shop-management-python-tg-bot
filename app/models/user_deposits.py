"""User deposits tracking model - one record per user with cumulative data."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class DepositTransaction(BaseModel):
    """Individual deposit transaction within user deposits."""
    
    invoice_id: int = Field(..., description="Crypto Pay invoice ID")
    amount: str = Field(..., description="Deposit amount")
    asset: str = Field(..., description="Deposit asset")
    paid_amount: Optional[str] = Field(None, description="Actually received amount")
    paid_asset: Optional[str] = Field(None, description="Actually received asset")
    usd_rate: Optional[str] = Field(None, description="USD rate at time of payment")
    fee_amount: Optional[float] = Field(None, description="Network fee")
    fee_asset: Optional[str] = Field(None, description="Fee asset")
    is_swapped: bool = Field(default=False, description="Whether payment was swapped")
    swapped_details: Optional[Dict[str, Any]] = Field(None, description="Swap details if applicable")
    deposit_date: datetime = Field(..., description="When deposit was made")
    
    class Config:
        use_enum_values = True


class UserDeposits(BaseModel):
    """User deposits tracking - one record per user with cumulative data."""
    
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: int = Field(..., description="Telegram user ID")
    
    # Cumulative totals
    total_deposits_count: int = Field(default=0, description="Total number of deposits")
    total_deposited_usdt: float = Field(default=0.0, description="Total deposited in USDT equivalent")
    total_fees_paid: float = Field(default=0.0, description="Total fees paid")
    
    # Asset breakdowns
    assets_deposited: Dict[str, float] = Field(default_factory=dict, description="Total per asset")
    
    # Transaction history
    transactions: List[DepositTransaction] = Field(default_factory=list, description="All deposit transactions")
    
    # Statistics
    first_deposit_date: Optional[datetime] = Field(None, description="Date of first deposit")
    last_deposit_date: Optional[datetime] = Field(None, description="Date of last deposit")
    largest_deposit_amount: float = Field(default=0.0, description="Largest single deposit in USDT")
    largest_deposit_invoice: Optional[int] = Field(None, description="Invoice ID of largest deposit")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class UserDepositsUpdate(BaseModel):
    """Update model for user deposits."""
    
    total_deposits_count: Optional[int] = None
    total_deposited_usdt: Optional[float] = None
    total_fees_paid: Optional[float] = None
    assets_deposited: Optional[Dict[str, float]] = None
    last_deposit_date: Optional[datetime] = None
    largest_deposit_amount: Optional[float] = None
    largest_deposit_invoice: Optional[int] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
