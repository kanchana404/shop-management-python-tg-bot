"""Admin command to manage crypto deposit limits."""

import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from app.db.user_repository import user_repo
from app.utils.rate_limiter import rate_limiter
from app.config.crypto_limits import CRYPTO_MINIMUMS, CRYPTO_MAXIMUMS_USD, format_crypto_minimum

logger = logging.getLogger(__name__)


@rate_limiter
async def cryptolimits_command_handler(client: Client, message: Message):
    """Handle /cryptolimits command to view and manage crypto deposit limits."""
    try:
        user_id = message.from_user.id
        user = await user_repo.get_by_tg_id(user_id)
        
        # Check if user is admin using the correct method
        from app.handlers.admin_handlers import is_admin
        if not await is_admin(user_id):
            await message.reply_text("❌ Access denied. Admin only.")
            return
        
        # Display current crypto limits
        text = "🪙 **Crypto Deposit Limits**\n\n"
        text += "**Current Minimums:**\n"
        
        for asset, minimum in CRYPTO_MINIMUMS.items():
            formatted_min = format_crypto_minimum(asset)
            text += f"• {asset}: {formatted_min}\n"
        
        text += "\n**Current Maximums:**\n"
        for asset, maximum in CRYPTO_MAXIMUMS_USD.items():
            text += f"• {asset}: ${maximum:,}\n"
        
        text += "\n**💡 To change limits:**\n"
        text += "Edit `app/config/crypto_limits.py` file\n"
        text += "Then restart the bot.\n\n"
        text += "**📊 Current Limits Summary:**\n"
        text += "• BTC: 0.00001 BTC (~$0.50)\n"
        text += "• ETH: 0.001 ETH (~$2)\n"
        text += "• USDT/USDC: 1.0 (~$1)\n"
        text += "• TON: 0.1 (~$0.50)\n"
        text += "• LTC: 0.01 (~$0.50)\n"
        text += "• BNB: 0.01 (~$5)\n"
        text += "• TRX: 10.0 (~$1)\n"
        
        await message.reply_text(text)
        
    except Exception as e:
        logger.error(f"Error in cryptolimits command: {e}")
        await message.reply_text("❌ An error occurred")
