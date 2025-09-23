"""Scheduled message service."""

from datetime import datetime
from typing import List
from app.db.scheduled_message_repository import scheduled_message_repo
from app.db.user_repository import user_repo
from app.models.scheduled_message import ScheduledMessage
import logging

logger = logging.getLogger(__name__)


class ScheduledMessageService:
    """Service for managing scheduled messages."""
    
    async def check_and_send_pending_messages(self) -> int:
        """Check for pending messages and send them."""
        try:
            # Get messages that are ready to be sent
            pending_messages = await scheduled_message_repo.get_pending_messages()
            
            if not pending_messages:
                return 0
            
            total_sent = 0
            
            for message in pending_messages:
                try:
                    sent_count = await self._send_scheduled_message(message)
                    total_sent += sent_count
                    
                except Exception as e:
                    logger.error(f"Error sending scheduled message {message.id}: {e}")
                    # Mark as sent with error to prevent retry loops
                    await scheduled_message_repo.mark_as_sent(message.id, 0, 1)
            
            if total_sent > 0:
                logger.info(f"Sent {total_sent} scheduled messages to users")
            
            return total_sent
            
        except Exception as e:
            logger.error(f"Error checking pending messages: {e}")
            return 0
    
    async def _send_scheduled_message(self, message: ScheduledMessage) -> int:
        """Send a scheduled message to users."""
        try:
            from app.bot import bot
            
            if not bot.active_clients:
                logger.warning("No active bot clients available for sending scheduled message")
                await scheduled_message_repo.mark_as_sent(message.id, 0, 1)
                return 0
            
            client = bot.active_clients[0]
            
            # Get target users
            if message.target_users:
                # Send to specific users
                target_user_ids = message.target_users
            else:
                # Send to all active users
                users = await user_repo.get_active_users()
                target_user_ids = [user.tg_id for user in users]
            
            if not target_user_ids:
                logger.warning("No target users found for scheduled message")
                await scheduled_message_repo.mark_as_sent(message.id, 0, 0)
                return 0
            
            # Send messages
            successful_sends = 0
            failed_sends = 0
            
            for user_id in target_user_ids:
                try:
                    await client.send_message(user_id, message.message)
                    successful_sends += 1
                    
                    # Small delay to avoid rate limits
                    import asyncio
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Failed to send scheduled message to user {user_id}: {e}")
                    failed_sends += 1
            
            # Mark as sent
            await scheduled_message_repo.mark_as_sent(
                message.id, 
                successful_sends, 
                failed_sends
            )
            
            logger.info(f"Scheduled message sent to {successful_sends} users, {failed_sends} failed")
            return successful_sends
            
        except Exception as e:
            logger.error(f"Error sending scheduled message: {e}")
            await scheduled_message_repo.mark_as_sent(message.id, 0, 1)
            return 0


# Global service instance
scheduled_message_service = ScheduledMessageService()

