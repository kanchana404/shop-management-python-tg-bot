"""Cart model and schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CartItem(BaseModel):
    """Cart item model."""
    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name (snapshot)")
    price: float = Field(..., description="Product price at time of adding (snapshot)")
    quantity: int = Field(default=1, description="Quantity in cart")
    total_price: float = Field(..., description="Total price for this item")
    
    def __init__(self, **data):
        """Initialize cart item with calculated total."""
        super().__init__(**data)
        if 'total_price' not in data:
            self.total_price = self.price * self.quantity


class Cart(BaseModel):
    """Cart model."""
    id: Optional[str] = Field(None, alias="_id")
    user_id: int = Field(..., description="User's Telegram ID")
    items: List[CartItem] = Field(default_factory=list, description="Cart items")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def total_amount(self) -> float:
        """Calculate total cart amount."""
        return sum(item.total_price for item in self.items)
    
    @property
    def total_items(self) -> int:
        """Calculate total number of items."""
        return sum(item.quantity for item in self.items)
    
    class Config:
        """Pydantic config."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        
    def __init__(self, **data):
        """Initialize cart with ObjectId conversion."""
        # Convert ObjectId to string if present
        if '_id' in data and data['_id'] is not None:
            from bson import ObjectId
            if isinstance(data['_id'], ObjectId):
                data['_id'] = str(data['_id'])
        super().__init__(**data)


class CartItemAdd(BaseModel):
    """Schema for adding item to cart."""
    product_id: str
    quantity: int = 1


class CartItemUpdate(BaseModel):
    """Schema for updating cart item."""
    quantity: int
