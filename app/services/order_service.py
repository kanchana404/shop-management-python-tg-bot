"""Order service."""

from typing import List, Optional
from datetime import datetime, timedelta
from app.models import Order, OrderCreate, OrderUpdate, OrderStatus, User
# db will be imported later to avoid circular imports
from app.services.cart_service import cart_service
from app.db.user_repository import user_repo
from app.db.product_repository import product_repo
import logging

logger = logging.getLogger(__name__)


class OrderService:
    """Service for managing orders."""
    
    def __init__(self):
        self.collection = None
    
    def _get_collection(self):
        """Lazy load the database collection."""
        if self.collection is None:
            from app.db import db
            self.collection = db.db.orders
        return self.collection
    
    async def create_order_from_cart(self, user: User) -> Optional[Order]:
        """Create an order from user's cart."""
        try:
            # Get cart
            cart = await cart_service.get_or_create_cart(user.tg_id)
            
            if not cart.items:
                return None  # Empty cart
            
            # Validate cart availability
            unavailable_items = await cart_service.validate_cart_availability(user.tg_id)
            if unavailable_items:
                return None  # Some items unavailable
            
            # Check user balance
            if user.balance < cart.total_amount:
                return None  # Insufficient balance
            
            # Deduct balance
            await user_repo.update_balance(user.tg_id, -cart.total_amount)
            
            # Decrease product quantities
            for item in cart.items:
                await product_repo.decrease_quantity(item.product_id, item.quantity)
            
            # Create order
            order_data = OrderCreate(
                user_id=user.tg_id,
                items=cart.items,
                total_amount=cart.total_amount,
                payment_method="balance"
            )
            
            # Use model_dump to ensure all fields including defaults are included
            order_dict = order_data.model_dump(by_alias=True)
            
            # Ensure enum values are converted to strings for MongoDB storage
            if 'status' in order_dict and hasattr(order_dict['status'], 'value'):
                order_dict['status'] = order_dict['status'].value
            collection = self._get_collection()
            result = await collection.insert_one(order_dict)
            
            # Clear cart
            await cart_service.clear_cart(user.tg_id)
            
            # Get created order
            order_doc = await collection.find_one({"_id": result.inserted_id})
            if order_doc:
                # Convert ObjectId to string for Pydantic validation
                order_doc["_id"] = str(order_doc["_id"])
                return Order(**order_doc)
            return None
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return None
    
    async def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        try:
            from bson import ObjectId
            collection = self._get_collection()
            order_doc = await collection.find_one({"_id": ObjectId(order_id)})
            if order_doc:
                order_doc["_id"] = str(order_doc["_id"])
                return Order(**order_doc)
            return None
        except Exception as e:
            logger.error(f"Error getting order: {e}")
            return None
    
    async def get_user_orders(
        self,
        user_id: int,
        limit: int = 20,
        skip: int = 0
    ) -> List[Order]:
        """Get user's orders."""
        try:
            collection = self._get_collection()
            cursor = collection.find({"user_id": user_id})
            cursor = cursor.sort("created_at", -1).skip(skip).limit(limit)
            
            orders = []
            async for order_doc in cursor:
                order_doc["_id"] = str(order_doc["_id"])
                orders.append(Order(**order_doc))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error getting user orders: {e}")
            return []
    
    async def update_order_status(self, order_id: str, status: OrderStatus) -> Optional[Order]:
        """Update order status."""
        try:
            from bson import ObjectId
            
            update_data = OrderUpdate(status=status)
            # Ensure updated_at is always set to current time
            update_dict = update_data.model_dump(exclude_unset=True)
            update_dict['updated_at'] = datetime.utcnow()
            
            collection = self._get_collection()
            result = await collection.update_one(
                {"_id": ObjectId(order_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count:
                return await self.get_order_by_id(order_id)
            return None
            
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            return None
    
    async def update_order(self, order_id: str, update_data: OrderUpdate) -> bool:
        """Update order with given data."""
        try:
            from bson import ObjectId
            
            # Ensure updated_at is always set to current time
            update_dict = update_data.model_dump(exclude_unset=True)
            update_dict['updated_at'] = datetime.utcnow()
            
            collection = self._get_collection()
            result = await collection.update_one(
                {"_id": ObjectId(order_id)},
                {"$set": update_dict}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating order: {e}")
            return False
    
    async def refund_order(self, order_id: str) -> bool:
        """Refund an order."""
        try:
            order = await self.get_order_by_id(order_id)
            if not order:
                return False
            
            # Update order status
            await self.update_order_status(order_id, OrderStatus.REFUNDED)
            
            # Refund balance to user
            await user_repo.update_balance(order.user_id, order.total_amount)
            
            # Restore product quantities
            for item in order.items:
                await product_repo.increase_quantity(item.product_id, item.quantity)
            
            return True
            
        except Exception as e:
            logger.error(f"Error refunding order: {e}")
            return False
    
    async def get_orders_by_status(
        self,
        status: OrderStatus,
        limit: int = 50,
        skip: int = 0
    ) -> List[Order]:
        """Get orders by status."""
        try:
            collection = self._get_collection()
            cursor = collection.find({"status": status.value})
            cursor = cursor.sort("created_at", -1).skip(skip).limit(limit)
            
            orders = []
            async for order_doc in cursor:
                order_doc["_id"] = str(order_doc["_id"])
                orders.append(Order(**order_doc))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error getting orders by status: {e}")
            return []
    
    async def get_order_stats(self, days: int = 30) -> dict:
        """Get order statistics."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Pipeline for aggregation
            pipeline = [
                {"$match": {"created_at": {"$gte": start_date}}},
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total_amount": {"$sum": "$total_amount"}
                }}
            ]
            
            stats = {
                "total_orders": 0,
                "total_revenue": 0.0,
                "by_status": {}
            }
            
            collection = self._get_collection()
            async for result in collection.aggregate(pipeline):
                status = result["_id"]
                count = result["count"]
                amount = result["total_amount"]
                
                stats["total_orders"] += count
                stats["total_revenue"] += amount
                stats["by_status"][status] = {
                    "count": count,
                    "total_amount": amount
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting order stats: {e}")
            return {}
    
    async def get_today_orders_count(self) -> int:
        """Get today's orders count."""
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            collection = self._get_collection()
            return await collection.count_documents({
                "created_at": {"$gte": today_start}
            })
        except Exception as e:
            logger.error(f"Error getting today's orders count: {e}")
            return 0
    
    async def get_today_revenue(self) -> float:
        """Get today's revenue."""
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            pipeline = [
                {"$match": {
                    "created_at": {"$gte": today_start},
                    "status": {"$nin": [OrderStatus.CANCELLED.value, OrderStatus.REFUNDED.value]}
                }},
                {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
            ]
            
            collection = self._get_collection()
            result = await collection.aggregate(pipeline).to_list(1)
            return result[0]["total"] if result else 0.0
            
        except Exception as e:
            logger.error(f"Error getting today's revenue: {e}")
            return 0.0
    
    async def get_recent_orders(self, limit: int = 10) -> List[Order]:
        """Get recent orders."""
        try:
            collection = self._get_collection()
            cursor = collection.find({}).sort("created_at", -1).limit(limit)
            orders = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                orders.append(Order(**doc))
            return orders
        except Exception as e:
            logger.error(f"Error getting recent orders: {e}")
            return []


# Service instance
order_service = OrderService()
