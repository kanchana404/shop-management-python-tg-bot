"""Cart service."""

from typing import List, Optional
from app.models import Cart, CartItem, CartItemAdd, Product
# db will be imported later to avoid circular imports
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CartService:
    """Service for managing shopping carts."""
    
    def __init__(self):
        self.collection = None
    
    def _get_collection(self):
        """Lazy load the database collection."""
        if self.collection is None:
            from app.db import db
            self.collection = db.db.carts
        return self.collection
    
    async def get_or_create_cart(self, user_id: int) -> Cart:
        """Get or create a cart for the user."""
        collection = self._get_collection()
        cart_doc = await collection.find_one({"user_id": user_id})
        
        if cart_doc:
            return Cart(**cart_doc)
        
        # Create new cart
        cart = Cart(user_id=user_id)
        cart_data = cart.model_dump(by_alias=True)  # Don't exclude unset to include items field
        result = await collection.insert_one(cart_data)
        
        cart_doc = await collection.find_one({"_id": result.inserted_id})
        return Cart(**cart_doc)
    
    async def add_item(self, user_id: int, product: Product, quantity: int = 1) -> bool:
        """Add item to cart."""
        try:
            logger.info(f"Adding item to cart: product={product.name}, quantity={quantity}, available_stock={product.quantity}")
            cart = await self.get_or_create_cart(user_id)
            
            # Check if item already exists in cart
            for item in cart.items:
                if item.product_id == str(product.id):
                    # Update quantity
                    new_quantity = item.quantity + quantity
                    if new_quantity > product.quantity:
                        logger.warning(f"Not enough stock for update: requested={new_quantity}, available={product.quantity}")
                        return False  # Not enough stock
                    
                    item.quantity = new_quantity
                    item.total_price = item.price * item.quantity
                    break
            else:
                # Add new item
                if quantity > product.quantity:
                    logger.warning(f"Not enough stock: requested={quantity}, available={product.quantity}")
                    return False  # Not enough stock
                
                cart_item = CartItem(
                    product_id=str(product.id),
                    product_name=product.name,
                    price=product.price,
                    quantity=quantity,
                    total_price=product.price * quantity
                )
                cart.items.append(cart_item)
            
            # Update cart
            cart.updated_at = datetime.utcnow()
            collection = self._get_collection()
            
            # Exclude _id field from update to avoid immutable field error
            update_data = cart.model_dump(by_alias=True)  # Don't exclude unset to include items field
            update_data.pop('_id', None)  # Remove _id if present
            
            await collection.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding item to cart: {e}")
            return False
    
    async def remove_item(self, user_id: int, product_id: str) -> bool:
        """Remove item from cart."""
        try:
            cart = await self.get_or_create_cart(user_id)
            
            # Find and remove item
            cart.items = [item for item in cart.items if item.product_id != product_id]
            cart.updated_at = datetime.utcnow()
            
            # Exclude _id field from update to avoid immutable field error
            update_data = cart.model_dump(by_alias=True)  # Don't exclude unset to include items field
            update_data.pop('_id', None)  # Remove _id if present
            
            collection = self._get_collection()
            await collection.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing item from cart: {e}")
            return False
    
    async def update_item_quantity(self, user_id: int, product_id: str, quantity: int) -> bool:
        """Update item quantity in cart."""
        try:
            cart = await self.get_or_create_cart(user_id)
            
            # Find and update item
            for item in cart.items:
                if item.product_id == product_id:
                    if quantity <= 0:
                        # Remove item if quantity is 0 or negative
                        cart.items = [i for i in cart.items if i.product_id != product_id]
                    else:
                        item.quantity = quantity
                        item.total_price = item.price * quantity
                    break
            
            cart.updated_at = datetime.utcnow()
            
            # Exclude _id field from update to avoid immutable field error
            update_data = cart.model_dump(by_alias=True)  # Don't exclude unset to include items field
            update_data.pop('_id', None)  # Remove _id if present
            
            collection = self._get_collection()
            await collection.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating item quantity: {e}")
            return False
    
    async def clear_cart(self, user_id: int) -> bool:
        """Clear all items from cart."""
        try:
            cart = await self.get_or_create_cart(user_id)
            cart.items = []
            cart.updated_at = datetime.utcnow()
            
            # Exclude _id field from update to avoid immutable field error
            update_data = cart.model_dump(by_alias=True)  # Don't exclude unset to include items field
            update_data.pop('_id', None)  # Remove _id if present
            
            collection = self._get_collection()
            await collection.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cart: {e}")
            return False
    
    async def get_cart_summary(self, user_id: int) -> dict:
        """Get cart summary with totals."""
        cart = await self.get_or_create_cart(user_id)
        
        return {
            "items_count": cart.total_items,
            "total_amount": cart.total_amount,
            "items": cart.items
        }
    
    async def validate_cart_availability(self, user_id: int) -> List[str]:
        """Validate cart items against current product availability."""
        from app.db.product_repository import product_repo
        
        cart = await self.get_or_create_cart(user_id)
        unavailable_items = []
        
        for item in cart.items:
            product = await product_repo.get_by_id(item.product_id)
            if not product or not product.is_active or product.quantity < item.quantity:
                unavailable_items.append(item.product_name)
        
        return unavailable_items


# Service instance
cart_service = CartService()
