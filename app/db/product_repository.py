"""Product repository."""

from typing import List, Optional
from .base_repository import BaseRepository
from .database import db
from app.models import Product, ProductCreate, ProductUpdate, ProductFilter, City, Area


class ProductRepository(BaseRepository[Product]):
    """Product repository."""
    
    def __init__(self):
        # Initialize with None, will be set when database is connected
        super().__init__(None, Product)
    
    def _get_collection(self):
        """Get the collection, initializing if needed."""
        if self.collection is None:
            from .database import db
            self.collection = db.db.products
        return self.collection
    
    async def create_product(self, product_data: ProductCreate) -> Product:
        """Create a new product."""
        return await self.create(product_data)
    
    async def get_products_by_location(
        self,
        city: City,
        area: Optional[Area] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 20
    ) -> List[Product]:
        """Get products by city and area."""
        filter_dict = {"city": city.value, "is_active": is_active}
        if area:
            filter_dict["area"] = area.value
        
        return await self.get_many(
            filter_dict=filter_dict,
            skip=skip,
            limit=limit,
            sort=[("created_at", -1)]
        )
    
    async def search_products(
        self,
        search_query: str,
        city: Optional[City] = None,
        area: Optional[Area] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 20
    ) -> List[Product]:
        """Search products by text."""
        filter_dict = {
            "$text": {"$search": search_query},
            "is_active": is_active
        }
        
        if city:
            filter_dict["city"] = city.value
        if area:
            filter_dict["area"] = area.value
        
        return await self.get_many(
            filter_dict=filter_dict,
            skip=skip,
            limit=limit,
            sort=[("score", {"$meta": "textScore"})]
        )
    
    async def get_low_stock_products(self, threshold: int = 5) -> List[Product]:
        """Get products with low stock."""
        return await self.get_many({
            "quantity": {"$lte": threshold},
            "is_active": True
        })
    
    async def update_product_quantity(self, product_id: str, quantity: int) -> Optional[Product]:
        """Update product quantity."""
        result = await self.collection.update_one(
            {"_id": self._to_object_id(product_id)},
            {"$set": {"quantity": quantity, "updated_at": self._utcnow()}}
        )
        
        if result.modified_count:
            return await self.get_by_id(product_id)
        return None
    
    async def decrease_quantity(self, product_id: str, amount: int) -> Optional[Product]:
        """Decrease product quantity."""
        result = await self.collection.update_one(
            {"_id": self._to_object_id(product_id), "quantity": {"$gte": amount}},
            {"$inc": {"quantity": -amount}, "$set": {"updated_at": self._utcnow()}}
        )
        
        if result.modified_count:
            return await self.get_by_id(product_id)
        return None
    
    async def increase_quantity(self, product_id: str, amount: int) -> Optional[Product]:
        """Increase product quantity."""
        result = await self.collection.update_one(
            {"_id": self._to_object_id(product_id)},
            {"$inc": {"quantity": amount}, "$set": {"updated_at": self._utcnow()}}
        )
        
        if result.modified_count:
            return await self.get_by_id(product_id)
        return None
    
    async def bulk_update_prices(self, price_multiplier: float, filter_dict: dict = None) -> int:
        """Bulk update product prices."""
        filter_dict = filter_dict or {}
        
        # Get products to update
        products = await self.get_many(filter_dict)
        
        # Update prices
        for product in products:
            new_price = round(product.price * price_multiplier, 2)
            await self.collection.update_one(
                {"_id": self._to_object_id(product.id)},
                {"$set": {"price": new_price, "updated_at": self._utcnow()}}
            )
        
        return len(products)
    
    async def toggle_active_status(self, product_id: str) -> Optional[Product]:
        """Toggle product active status."""
        product = await self.get_by_id(product_id)
        if not product:
            return None
        
        result = await self.collection.update_one(
            {"_id": self._to_object_id(product_id)},
            {"$set": {"is_active": not product.is_active, "updated_at": self._utcnow()}}
        )
        
        if result.modified_count:
            return await self.get_by_id(product_id)
        return None
    
    async def get_products_count_by_city(self) -> dict:
        """Get product count by city."""
        pipeline = [
            {"$match": {"is_active": True}},
            {"$group": {"_id": "$city", "count": {"$sum": 1}}}
        ]
        
        result = {}
        async for doc in self.collection.aggregate(pipeline):
            result[doc["_id"]] = doc["count"]
        
        return result
    
    def _to_object_id(self, doc_id: str):
        """Convert string ID to ObjectId."""
        from bson import ObjectId
        return ObjectId(doc_id)
    
    def _utcnow(self):
        """Get current UTC datetime."""
        from datetime import datetime
        return datetime.utcnow()


# Repository instance
product_repo = ProductRepository()
