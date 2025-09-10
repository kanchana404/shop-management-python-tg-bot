"""Admin commands for managing user activity tracking."""

import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from app.db.user_repository import user_repo
from app.utils.rate_limiter import rate_limiter
from app.utils.user_activity import user_activity_tracker

logger = logging.getLogger(__name__)


@rate_limiter
async def activity_command_handler(client: Client, message: Message):
    """Handle /activity command to view and manage activity settings."""
    try:
        user_id = message.from_user.id
        user = await user_repo.get_by_tg_id(user_id)
        
        # Check if user is admin using the correct method
        from app.handlers.admin_handlers import is_admin
        if not await is_admin(user_id):
            await message.reply_text("❌ Access denied. Admin only.")
            return
        
        # Check if setting threshold
        args = message.text.split()
        if len(args) == 2:
            try:
                minutes = int(args[1])
                if 1 <= minutes <= 60:
                    user_activity_tracker.set_inactive_threshold(minutes)
                    await message.reply_text(f"✅ Inactivity threshold set to {minutes} minutes")
                else:
                    await message.reply_text("❌ Threshold must be between 1 and 60 minutes")
            except ValueError:
                await message.reply_text("❌ Invalid number. Use: /activity [minutes]")
            return
        
        # Show current settings
        text = "⏰ **User Activity Settings**\n\n"
        text += f"📊 **Current Threshold:** {user_activity_tracker._inactive_threshold_minutes} minutes\n"
        text += f"👥 **Tracked Users:** {len(user_activity_tracker._last_activity)}\n\n"
        text += "**How it works:**\n"
        text += "• Users see their balance when they return after being inactive\n"
        text += "• Balance is shown in both EUR and USDT\n"
        text += "• Activity is tracked on all bot interactions\n\n"
        text += "**Commands:**\n"
        text += "• `/activity` - Show current settings\n"
        text += "• `/activity [minutes]` - Set threshold (1-60 min)\n\n"
        text += "**Examples:**\n"
        text += "• `/activity 5` - Show balance after 5 min inactivity\n"
        text += "• `/activity 10` - Show balance after 10 min inactivity\n"
        
        await message.reply_text(text)
        
    except Exception as e:
        logger.error(f"Error in activity command: {e}")
        await message.reply_text("❌ An error occurred")
