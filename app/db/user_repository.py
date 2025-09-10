"""User repository."""

import logging
from typing import List, Optional
from .base_repository import BaseRepository
from .database import db
from app.models import User, UserCreate, UserUpdate, UserRole


class UserRepository(BaseRepository[User]):
    """User repository."""
    
    def __init__(self):
        # Initialize with None, will be set when database is connected
        super().__init__(None, User)
    
    def _get_collection(self):
        """Get the collection, initializing if needed."""
        if self.collection is None:
            from .database import db
            self.collection = db.db.users
        return self.collection
    
    async def get_by_tg_id(self, tg_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        return await self.get_by_filter({"tg_id": tg_id})
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        return await self.create(user_data)
    
    async def update_user(self, tg_id: int, update_data: UserUpdate) -> Optional[User]:
        """Update user by Telegram ID."""
        collection = self._get_collection()
        result = await collection.update_one(
            {"tg_id": tg_id},
            {"$set": update_data.dict(exclude_unset=True)}
        )
        
        if result.modified_count:
            return await self.get_by_tg_id(tg_id)
        return None
    
    async def update_balance(self, tg_id: int, amount: float) -> Optional[User]:
        """Update user balance."""
        collection = self._get_collection()
        result = await collection.update_one(
            {"tg_id": tg_id},
            {"$inc": {"balance": amount}, "$set": {"updated_at": self._utcnow()}}
        )
        
        if result.modified_count:
            return await self.get_by_tg_id(tg_id)
        return None
    
    async def set_language(self, tg_id: int, language_code: str) -> Optional[User]:
        """Set user language."""
        collection = self._get_collection()
        result = await collection.update_one(
            {"tg_id": tg_id},
            {"$set": {"language_code": language_code, "updated_at": self._utcnow()}}
        )
        
        if result.modified_count:
            return await self.get_by_tg_id(tg_id)
        return None
    
    async def ban_user(self, tg_id: int, reason: str = None) -> Optional[User]:
        """Ban a user."""
        collection = self._get_collection()
        result = await collection.update_one(
            {"tg_id": tg_id},
            {"$set": {
                "is_banned": True,
                "ban_reason": reason,
                "updated_at": self._utcnow()
            }}
        )
        
        if result.modified_count:
            return await self.get_by_tg_id(tg_id)
        return None
    
    async def unban_user(self, tg_id: int) -> Optional[User]:
        """Unban a user."""
        collection = self._get_collection()
        result = await collection.update_one(
            {"tg_id": tg_id},
            {"$set": {
                "is_banned": False,
                "ban_reason": None,
                "updated_at": self._utcnow()
            }}
        )
        
        if result.modified_count:
            return await self.get_by_tg_id(tg_id)
        return None
    
    async def add_role(self, tg_id: int, role: UserRole) -> Optional[User]:
        """Add role to user."""
        collection = self._get_collection()
        result = await collection.update_one(
            {"tg_id": tg_id},
            {"$addToSet": {"roles": role.value}, "$set": {"updated_at": self._utcnow()}}
        )
        
        if result.modified_count:
            return await self.get_by_tg_id(tg_id)
        return None
    
    async def remove_role(self, tg_id: int, role: UserRole) -> Optional[User]:
        """Remove role from user."""
        collection = self._get_collection()
        result = await collection.update_one(
            {"tg_id": tg_id},
            {"$pull": {"roles": role.value}, "$set": {"updated_at": self._utcnow()}}
        )
        
        if result.modified_count:
            return await self.get_by_tg_id(tg_id)
        return None
    
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Get all users with a specific role."""
        try:
            collection = self._get_collection()
            cursor = collection.find({"roles": role.value})
            
            users = []
            async for user_doc in cursor:
                user_doc["_id"] = str(user_doc["_id"])
                users.append(User(**user_doc))
            
            return users
            
        except Exception as e:
            logger.error(f"Error getting users by role {role}: {e}")
            return []
    
    async def get_admins(self) -> List[User]:
        """Get all admin users."""
        return await self.get_many({
            "roles": {"$in": [UserRole.OWNER.value, UserRole.ADMIN.value, UserRole.STAFF.value]}
        })
    
    async def get_active_users_count(self) -> int:
        """Get count of active (non-banned) users."""
        return await self.count({"is_banned": {"$ne": True}})
    
    def _utcnow(self):
        """Get current UTC datetime."""
        from datetime import datetime
        return datetime.utcnow()
    
    async def update_user_activity(self, user_id: int):
        """Update user's last activity timestamp (updated_at field)."""
        try:
            collection = self._get_collection()
            result = await collection.update_one(
                {"tg_id": user_id},
                {"$set": {"updated_at": self._utcnow()}}
            )
            
            if result.modified_count > 0:
                logging.debug(f"Updated activity timestamp for user {user_id}")
            else:
                logging.warning(f"User {user_id} not found when updating activity")
                
        except Exception as e:
            logging.error(f"Error updating user activity for {user_id}: {e}")
            raise


# Repository instance
user_repo = UserRepository()
