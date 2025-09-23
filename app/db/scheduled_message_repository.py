"""Scheduled message repository."""

from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from app.db.base_repository import BaseRepository
from app.models.scheduled_message import ScheduledMessage, ScheduledMessageCreate, ScheduledMessageUpdate
import logging

logger = logging.getLogger(__name__)


class ScheduledMessageRepository(BaseRepository[ScheduledMessage]):
    """Repository for scheduled messages."""
    
    def __init__(self):
        # Initialize with None, will be set when database is connected
        super().__init__(None, ScheduledMessage)
    
    def _get_collection(self):
        """Get the collection, initializing if needed."""
        if self.collection is None:
            from app.db.database import db
            self.collection = db.db.scheduled_messages
        return self.collection
    
    async def create_scheduled_message(self, message_data: ScheduledMessageCreate) -> ScheduledMessage:
        """Create a new scheduled message."""
        try:
            collection = self._get_collection()
            message_dict = message_data.model_dump()
            message_dict["created_at"] = datetime.utcnow()
            
            result = await collection.insert_one(message_dict)
            message_dict["_id"] = str(result.inserted_id)
            
            logger.info(f"Created scheduled message for {message_data.scheduled_time}")
            return ScheduledMessage(**message_dict)
            
        except Exception as e:
            logger.error(f"Error creating scheduled message: {e}")
            raise
    
    async def get_pending_messages(self, current_time: datetime = None) -> List[ScheduledMessage]:
        """Get messages that are ready to be sent."""
        try:
            if current_time is None:
                current_time = datetime.utcnow()
            
            query = {
                "is_sent": False,
                "is_active": True,
                "scheduled_time": {"$lte": current_time}
            }
            
            collection = self._get_collection()
            cursor = collection.find(query)
            messages = []
            
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                messages.append(ScheduledMessage(**doc))
            
            logger.info(f"Found {len(messages)} pending scheduled messages")
            return messages
            
        except Exception as e:
            logger.error(f"Error getting pending messages: {e}")
            return []
    
    async def mark_as_sent(self, message_id: str, recipients_count: int = 0, errors_count: int = 0) -> bool:
        """Mark a scheduled message as sent."""
        try:
            update_data = {
                "is_sent": True,
                "sent_at": datetime.utcnow(),
                "recipients_count": recipients_count,
                "errors_count": errors_count
            }
            
            collection = self._get_collection()
            result = await collection.update_one(
                {"_id": ObjectId(message_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Marked scheduled message {message_id} as sent to {recipients_count} users")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking message as sent: {e}")
            return False
    
    async def get_scheduled_messages(self, include_sent: bool = True, limit: int = 50) -> List[ScheduledMessage]:
        """Get scheduled messages with optional filtering."""
        try:
            query = {}
            if not include_sent:
                query["is_sent"] = False
            
            collection = self._get_collection()
            cursor = collection.find(query).sort("scheduled_time", -1).limit(limit)
            messages = []
            
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                messages.append(ScheduledMessage(**doc))
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting scheduled messages: {e}")
            return []
    
    async def update_scheduled_message(self, message_id: str, update_data: ScheduledMessageUpdate) -> bool:
        """Update a scheduled message."""
        try:
            # Only allow updates to unsent messages
            query = {
                "_id": ObjectId(message_id),
                "is_sent": False
            }
            
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            
            if not update_dict:
                return False
            
            collection = self._get_collection()
            result = await collection.update_one(query, {"$set": update_dict})
            
            if result.modified_count > 0:
                logger.info(f"Updated scheduled message {message_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating scheduled message: {e}")
            return False
    
    async def delete_scheduled_message(self, message_id: str) -> bool:
        """Delete a scheduled message (only if not sent)."""
        try:
            query = {
                "_id": ObjectId(message_id),
                "is_sent": False
            }
            
            collection = self._get_collection()
            result = await collection.delete_one(query)
            
            if result.deleted_count > 0:
                logger.info(f"Deleted scheduled message {message_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting scheduled message: {e}")
            return False


# Global repository instance
scheduled_message_repo = ScheduledMessageRepository()
