"""Schedule command handler for creating scheduled messages."""

import logging
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from app.db.scheduled_message_repository import scheduled_message_repo
from app.models.scheduled_message import ScheduledMessageCreate
from app.utils.rate_limiter import rate_limiter
from app.handlers.admin_handlers import is_admin

logger = logging.getLogger(__name__)


@rate_limiter
async def schedule_command_handler(client: Client, message: Message):
    """Handle /schedule command for creating scheduled messages."""
    try:
        user_id = message.from_user.id
        
        # Check admin privileges
        if not await is_admin(user_id):
            await message.reply_text("❌ Access denied. You don't have admin privileges.")
            return
        
        # Parse command
        command_text = message.text.strip()
        if not command_text.startswith("/schedule "):
            await message.reply_text(
                "❌ **Invalid format**\n\n"
                "**Usage:** `/schedule YYYY-MM-DD HH:MM Your message here`\n\n"
                "**Examples:**\n"
                "• `/schedule 2024-12-25 09:00 🎄 Merry Christmas! Special offers today!`\n"
                "• `/schedule 2024-01-01 00:00 🎆 Happy New Year! Check out our New Year deals!`\n\n"
                "**Notes:**\n"
                "• Use 24-hour format for time\n"
                "• Date must be in the future\n"
                "• Maximum 30 days in advance"
            )
            return
        
        # Extract datetime and message
        try:
            parts = command_text[10:].strip().split(" ", 2)  # Remove "/schedule "
            
            if len(parts) < 3:
                await message.reply_text("❌ Please provide date, time, and message content.")
                return
            
            date_str = parts[0]
            time_str = parts[1]
            message_content = parts[2]
            
            # Parse datetime
            datetime_str = f"{date_str} {time_str}"
            scheduled_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            
            # Validate datetime
            now = datetime.utcnow()
            
            if scheduled_time <= now:
                await message.reply_text("❌ Scheduled time must be in the future.")
                return
            
            # Check if too far in the future (30 days max)
            max_future = now + timedelta(days=30)
            if scheduled_time > max_future:
                await message.reply_text("❌ Cannot schedule messages more than 30 days in advance.")
                return
            
            # Create scheduled message
            scheduled_message_data = ScheduledMessageCreate(
                message=message_content,
                scheduled_time=scheduled_time,
                created_by=user_id
            )
            
            scheduled_message = await scheduled_message_repo.create_scheduled_message(scheduled_message_data)
            
            if scheduled_message:
                confirmation_text = (
                    "✅ **Message Scheduled Successfully!**\n\n"
                    f"📅 **Date:** {scheduled_time.strftime('%Y-%m-%d')}\n"
                    f"⏰ **Time:** {scheduled_time.strftime('%H:%M')} UTC\n"
                    f"📝 **Message:** {message_content[:100]}{'...' if len(message_content) > 100 else ''}\n"
                    f"🆔 **ID:** `{scheduled_message.id}`\n\n"
                    f"📤 **Recipients:** All active users\n"
                    f"⚡ **Status:** Scheduled\n\n"
                    "The message will be automatically sent at the specified time."
                )
                
                await message.reply_text(confirmation_text)
                logger.info(f"Admin {user_id} scheduled message for {scheduled_time}")
            else:
                await message.reply_text("❌ Failed to schedule message. Please try again.")
                
        except ValueError as e:
            await message.reply_text(
                "❌ **Invalid date/time format**\n\n"
                "Please use: `YYYY-MM-DD HH:MM`\n\n"
                "**Examples:**\n"
                "• `2024-12-25 09:00`\n"
                "• `2024-01-01 12:30`\n\n"
                "Make sure to use 24-hour format!"
            )
            
    except Exception as e:
        logger.error(f"Error in schedule command handler: {e}")
        await message.reply_text("❌ An error occurred while scheduling the message.")

