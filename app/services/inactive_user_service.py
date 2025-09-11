"""Service for checking and notifying inactive users."""

import logging
from datetime import datetime, timedelta
from typing import List
from app.db.user_repository import user_repo
from app.models import User
from pyrogram import Client

logger = logging.getLogger(__name__)

class InactiveUserService:
    """Service to check for inactive users and send reminders."""
    
    def __init__(self):
        self.inactive_threshold_minutes = 5
        
    async def check_and_notify_inactive_users(self, bot_client: Client) -> None:
        """Check all users for inactivity and send balance reminders."""
        try:
            current_time = datetime.utcnow()
            logger.info(f"🔍 Checking for inactive users at {current_time.strftime('%H:%M:%S')}")
            
            # Get all users from database
            all_users = await self._get_all_users()
            logger.info(f"📊 Found {len(all_users)} total users in database")
            
            inactive_users = []
            active_users = 0
            
            # Check each user for inactivity
            for user in all_users:
                if await self._is_user_inactive(user, current_time):
                    inactive_users.append(user)
                else:
                    active_users += 1
            
            logger.info(f"⏰ Inactive users (>{self.inactive_threshold_minutes}min): {len(inactive_users)}")
            logger.info(f"✅ Active users: {active_users}")
            
            # Send balance reminders to inactive users
            notifications_sent = 0
            for user in inactive_users:
                try:
                    success = await self._send_balance_reminder(bot_client, user)
                    if success:
                        notifications_sent += 1
                        # Note: We don't update user activity here - reminder_sent flag prevents spam
                        
                except Exception as e:
                    logger.error(f"❌ Failed to send reminder to user {user.tg_id}: {e}")
                    
            logger.info(f"📤 Balance reminders sent: {notifications_sent}/{len(inactive_users)}")
            
        except Exception as e:
            logger.error(f"❌ Error in inactive user check: {e}")
    
    async def _get_all_users(self) -> List[User]:
        """Get all users from database."""
        try:
            # We need to implement get_all_users in user_repo
            collection = user_repo._get_collection()
            cursor = collection.find({})
            
            users = []
            async for user_doc in cursor:
                user_doc["_id"] = str(user_doc["_id"])
                users.append(User(**user_doc))
                
            return users
            
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    async def _is_user_inactive(self, user: User, current_time: datetime) -> bool:
        """Check if user is inactive and hasn't received reminder yet."""
        if not user.updated_at:
            return False
            
        # Skip if reminder was already sent
        if getattr(user, 'reminder_sent', False):
            return False
            
        inactive_duration = current_time - user.updated_at
        is_inactive = inactive_duration >= timedelta(minutes=self.inactive_threshold_minutes)
        
        if is_inactive:
            logger.debug(f"👤 User {user.tg_id} ({user.first_name}) inactive for {inactive_duration}")
            
        return is_inactive
    
    async def _send_balance_reminder(self, bot_client: Client, user: User) -> bool:
        """Send inactivity reminder to user."""
        try:
            # Send the resource-saving reminder message
            reminder_message = (
                "I haven't received any message in a while so close the conversation to save resource "
                "if you want to start a new one send a new /start command"
            )
            
            await bot_client.send_message(
                chat_id=user.tg_id,
                text=reminder_message
            )
            
            # Mark reminder as sent in database
            await user_repo.set_reminder_sent(user.tg_id)
            
            logger.info(f"📤 Sent inactivity reminder to user {user.tg_id} ({user.first_name})")
            return True
                
        except Exception as e:
            logger.error(f"Failed to send reminder to user {user.tg_id}: {e}")
            return False
    
    def set_inactive_threshold(self, minutes: int):
        """Set the inactivity threshold in minutes."""
        self.inactive_threshold_minutes = minutes
        logger.info(f"⏰ Inactive threshold set to {minutes} minutes")

# Service instance
inactive_user_service = InactiveUserService()
