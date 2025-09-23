"""Message deduplication utility to prevent duplicate messages."""

import asyncio
from typing import Dict, Set
from datetime import datetime, timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)


class MessageDeduplicator:
    """Prevents duplicate messages from being sent to users."""
    
    def __init__(self):
        self._recent_messages: Dict[int, Set[str]] = {}  # user_id -> set of message hashes
        self._cleanup_interval = 300  # 5 minutes
        self._message_ttl = 30  # 30 seconds
        self._running_cleanup = False
    
    def _generate_message_hash(self, user_id: int, message_content: str, message_type: str = "general") -> str:
        """Generate a hash for the message to detect duplicates."""
        content = f"{user_id}:{message_type}:{message_content[:100]}"  # First 100 chars
        return hashlib.md5(content.encode()).hexdigest()
    
    async def should_send_message(self, user_id: int, message_content: str, message_type: str = "general") -> bool:
        """
        Check if message should be sent (not a duplicate).
        
        Args:
            user_id: Target user ID
            message_content: Message content to check
            message_type: Type of message (start, crypto_invoice, etc.)
            
        Returns:
            True if message should be sent, False if it's a duplicate
        """
        try:
            message_hash = self._generate_message_hash(user_id, message_content, message_type)
            
            # Initialize user's message set if not exists
            if user_id not in self._recent_messages:
                self._recent_messages[user_id] = set()
            
            # Check if this message was recently sent
            if message_hash in self._recent_messages[user_id]:
                logger.warning(f"Duplicate {message_type} message blocked for user {user_id}")
                return False
            
            # Add message hash to recent messages
            self._recent_messages[user_id].add(message_hash)
            
            # Start cleanup task if not running
            if not self._running_cleanup:
                asyncio.create_task(self._cleanup_old_messages())
            
            return True
            
        except Exception as e:
            logger.error(f"Error in message deduplication: {e}")
            return True  # Allow message on error to avoid blocking legitimate messages
    
    async def _cleanup_old_messages(self):
        """Clean up old message hashes periodically."""
        if self._running_cleanup:
            return
            
        self._running_cleanup = True
        
        try:
            while True:
                await asyncio.sleep(self._cleanup_interval)
                
                # Clear all stored hashes (simple approach - in production you might want more sophisticated TTL)
                if self._recent_messages:
                    cleared_users = len(self._recent_messages)
                    self._recent_messages.clear()
                    logger.debug(f"Cleaned up message deduplication cache for {cleared_users} users")
                
        except Exception as e:
            logger.error(f"Error in message cleanup: {e}")
        finally:
            self._running_cleanup = False
    
    def clear_user_messages(self, user_id: int):
        """Clear recent messages for a specific user."""
        if user_id in self._recent_messages:
            del self._recent_messages[user_id]


# Global message deduplicator instance
message_deduplicator = MessageDeduplicator()

