"""User activity tracking for automatic balance display."""

import asyncio
from typing import Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class UserActivityTracker:
    """Tracks user activity to show balance after inactivity periods."""
    
    def __init__(self):
        self._last_activity: Dict[int, datetime] = {}
        self._inactive_threshold_minutes = 5
    
    async def update_activity(self, user_id: int):
        """Update user's last activity timestamp in database."""
        try:
            from app.db.user_repository import user_repo
            
            # Update database updated_at field
            await user_repo.update_user_activity(user_id)
            
            # Also update in-memory for backwards compatibility
            self._last_activity[user_id] = datetime.utcnow()
            logger.debug(f"Updated activity for user {user_id} in database")
            
        except Exception as e:
            logger.error(f"Error updating user activity in database: {e}")
            # Fallback to in-memory only
            self._last_activity[user_id] = datetime.utcnow()
    
    async def should_show_balance(self, user_id: int) -> bool:
        """Check if user should see automatic balance display using database."""
        try:
            from app.db.user_repository import user_repo
            
            user = await user_repo.get_by_tg_id(user_id)
            if not user:
                return False
            
            # Check if user was inactive based on database updated_at
            if user.updated_at:
                inactive_duration = datetime.utcnow() - user.updated_at
                
                # If user was inactive for threshold+ minutes, show balance
                if inactive_duration >= timedelta(minutes=self._inactive_threshold_minutes):
                    logger.info(f"User {user_id} was inactive for {inactive_duration}, showing balance")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking user activity from database: {e}")
            return False
    
    def set_inactive_threshold(self, minutes: int):
        """Set the inactivity threshold in minutes."""
        self._inactive_threshold_minutes = minutes
        logger.info(f"Inactivity threshold set to {minutes} minutes")
    
    def get_inactive_duration(self, user_id: int) -> timedelta:
        """Get how long user has been inactive."""
        if user_id not in self._last_activity:
            return timedelta(0)
        
        return datetime.utcnow() - self._last_activity[user_id]
    
    async def cleanup_old_activities(self):
        """Clean up old activity records (older than 24 hours)."""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        old_users = []
        
        for user_id, last_activity in self._last_activity.items():
            if last_activity < cutoff_time:
                old_users.append(user_id)
        
        for user_id in old_users:
            del self._last_activity[user_id]
        
        if old_users:
            logger.info(f"Cleaned up activity records for {len(old_users)} users")


# Global activity tracker instance
user_activity_tracker = UserActivityTracker()
