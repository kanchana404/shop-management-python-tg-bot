"""Database connection and setup."""

import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(settings.mongo_uri)
            self.db = self.client[settings.database_name]
            
            # Test connection
            await self.client.admin.command('ismaster')
            logger.info(f"Connected to MongoDB: {settings.database_name}")
            
            # Create indexes
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def _create_indexes(self):
        """Create database indexes for optimization."""
        try:
            # Users collection indexes
            await self.db.users.create_indexes([
                IndexModel([("tg_id", ASCENDING)], unique=True),
                IndexModel([("username", ASCENDING)]),
                IndexModel([("roles", ASCENDING)]),
                IndexModel([("is_banned", ASCENDING)]),
            ])
            
            # Products collection indexes
            await self.db.products.create_indexes([
                IndexModel([("city", ASCENDING), ("area", ASCENDING)]),
                IndexModel([("is_active", ASCENDING)]),
                IndexModel([("name", "text"), ("description", "text")]),
                IndexModel([("created_at", DESCENDING)]),
                IndexModel([("city", ASCENDING), ("area", ASCENDING), ("is_active", ASCENDING)]),
            ])
            
            # Carts collection indexes
            await self.db.carts.create_indexes([
                IndexModel([("user_id", ASCENDING)], unique=True),
                IndexModel([("updated_at", DESCENDING)]),
            ])
            
            # Orders collection indexes
            await self.db.orders.create_indexes([
                IndexModel([("user_id", ASCENDING)]),
                IndexModel([("status", ASCENDING)]),
                IndexModel([("created_at", DESCENDING)]),
                IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)]),
            ])
            
            # Deposits collection indexes
            await self.db.deposits.create_indexes([
                IndexModel([("user_id", ASCENDING)]),
                IndexModel([("status", ASCENDING)]),
                IndexModel([("created_at", DESCENDING)]),
                IndexModel([("txid", ASCENDING)]),
                IndexModel([("address", ASCENDING)]),
                IndexModel([("expires_at", ASCENDING)]),
            ])
            
            # Announcements collection indexes
            await self.db.announcements.create_indexes([
                IndexModel([("scheduled_at", ASCENDING)]),
                IndexModel([("status", ASCENDING)]),
                IndexModel([("type", ASCENDING)]),
            ])
            
            # Settings collection indexes
            await self.db.settings.create_indexes([
                IndexModel([("key", ASCENDING)], unique=True),
            ])
            
            # Audit logs collection indexes
            await self.db.audit_logs.create_indexes([
                IndexModel([("created_at", DESCENDING)]),
                IndexModel([("action", ASCENDING)]),
                IndexModel([("user_id", ASCENDING)]),
                IndexModel([("target_user_id", ASCENDING)]),
            ])
            
            # Invoices collection indexes
            await self.db.invoices.create_indexes([
                IndexModel([("invoice_id", ASCENDING)], unique=True),
                IndexModel([("user_id", ASCENDING)]),
                IndexModel([("status", ASCENDING)]),
                IndexModel([("type", ASCENDING)]),
                IndexModel([("created_at", DESCENDING)]),
                IndexModel([("expires_at", ASCENDING)]),
                IndexModel([("paid_at", DESCENDING)]),
                IndexModel([("user_id", ASCENDING), ("status", ASCENDING)]),
                IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("order_id", ASCENDING)]),
            ])
            
            # User deposits collection indexes
            await self.db.user_deposits.create_indexes([
                IndexModel([("user_id", ASCENDING)], unique=True),
                IndexModel([("total_deposited_usdt", DESCENDING)]),
                IndexModel([("total_deposits_count", DESCENDING)]),
                IndexModel([("last_deposit_date", DESCENDING)]),
                IndexModel([("transactions.invoice_id", ASCENDING)]),
                IndexModel([("transactions.deposit_date", DESCENDING)]),
            ])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise


# Global database instance
db = Database()





