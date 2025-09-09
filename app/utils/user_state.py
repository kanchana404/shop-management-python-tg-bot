"""User state management for bot interactions."""

import asyncio
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class UserStateManager:
    """Manages user states for multi-step interactions."""
    
    def __init__(self):
        self._states: Dict[int, Dict[str, Any]] = {}
        self._cleanup_task = None
    
    async def set_state(self, user_id: int, state: str, data: Optional[Dict[str, Any]] = None, timeout_minutes: int = 10):
        """Set user state with optional data and timeout."""
        try:
            if user_id not in self._states:
                self._states[user_id] = {}
            
            self._states[user_id].update({
                'current_state': state,
                'data': data or {},
                'timestamp': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(minutes=timeout_minutes)
            })
            
            logger.info(f"Set state for user {user_id}: {state}")
            
            # Start cleanup task if not running
            if not self._cleanup_task:
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        except Exception as e:
            logger.error(f"Error setting user state: {e}")
    
    async def get_state(self, user_id: int) -> Optional[str]:
        """Get current user state."""
        try:
            if user_id not in self._states:
                return None
            
            user_data = self._states[user_id]
            
            # Check if state expired
            if datetime.utcnow() > user_data.get('expires_at', datetime.utcnow()):
                await self.clear_state(user_id)
                return None
            
            return user_data.get('current_state')
        
        except Exception as e:
            logger.error(f"Error getting user state: {e}")
            return None
    
    async def get_state_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user state data."""
        try:
            if user_id not in self._states:
                return None
            
            user_data = self._states[user_id]
            
            # Check if state expired
            if datetime.utcnow() > user_data.get('expires_at', datetime.utcnow()):
                await self.clear_state(user_id)
                return None
            
            return user_data.get('data', {})
        
        except Exception as e:
            logger.error(f"Error getting user state data: {e}")
            return None
    
    async def clear_state(self, user_id: int):
        """Clear user state."""
        try:
            if user_id in self._states:
                del self._states[user_id]
                logger.info(f"Cleared state for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error clearing user state: {e}")
    
    async def is_in_state(self, user_id: int, state: str) -> bool:
        """Check if user is in specific state."""
        current_state = await self.get_state(user_id)
        return current_state == state
    
    async def _periodic_cleanup(self):
        """Periodically clean up expired states."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                current_time = datetime.utcnow()
                expired_users = []
                
                for user_id, user_data in self._states.items():
                    if current_time > user_data.get('expires_at', current_time):
                        expired_users.append(user_id)
                
                for user_id in expired_users:
                    await self.clear_state(user_id)
                
                if expired_users:
                    logger.info(f"Cleaned up {len(expired_users)} expired user states")
            
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")


# Global state manager instance
user_state_manager = UserStateManager()


# State constants
class UserStates:
    """User state constants."""
    CRYPTO_DEPOSIT_AMOUNT_INPUT = "crypto_deposit_amount_input"
    CRYPTO_ORDER_PAYMENT = "crypto_order_payment"
    ADMIN_BROADCAST = "admin_broadcast"
    ADMIN_PRODUCT_ADD = "admin_product_add"
