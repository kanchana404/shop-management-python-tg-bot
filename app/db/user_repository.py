"""User repository."""

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
        result = await self.collection.update_one(
            {"tg_id": tg_id},
            {"$set": update_data.dict(exclude_unset=True)}
        )
        
        if result.modified_count:
            return await self.get_by_tg_id(tg_id)
        return None
    
    async def update_balance(self, tg_id: int, amount: float) -> Optional[User]:
        """Update user balance."""
        result = await self.collection.update_one(
            {"tg_id": tg_id},
            {"$inc": {"balance": amount}, "$set": {"updated_at": self._utcnow()}}
        )
        
        if result.modified_count:
            return await self.get_by_tg_id(tg_id)
        return None
    
    async def set_language(self, tg_id: int, language_code: str) -> Optional[User]:
        """Set user language."""
        result = await self.collection.update_one(
            {"tg_id": tg_id},
            {"$set": {"language_code": language_code, "updated_at": self._utcnow()}}
        )
        
        if result.modified_count:
            return await self.get_by_tg_id(tg_id)
        return None
    
    async def ban_user(self, tg_id: int, reason: str = None) -> Optional[User]:
        """Ban a user."""
        result = await self.collection.update_one(
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
        result = await self.collection.update_one(
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
        result = await self.collection.update_one(
            {"tg_id": tg_id},
            {"$addToSet": {"roles": role.value}, "$set": {"updated_at": self._utcnow()}}
        )
        
        if result.modified_count:
            return await self.get_by_tg_id(tg_id)
        return None
    
    async def remove_role(self, tg_id: int, role: UserRole) -> Optional[User]:
        """Remove role from user."""
        result = await self.collection.update_one(
            {"tg_id": tg_id},
            {"$pull": {"roles": role.value}, "$set": {"updated_at": self._utcnow()}}
        )
        
        if result.modified_count:
            return await self.get_by_tg_id(tg_id)
        return None
    
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


# Repository instance
user_repo = UserRepository()
