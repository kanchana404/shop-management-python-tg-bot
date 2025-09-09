"""Handlers for deposits management and viewing."""

import logging
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from app.db.user_deposits_repository import user_deposits_repo
from app.db.user_repository import user_repo
from app.utils.decorators import rate_limiter, admin_required
from app.utils.i18n import get_user_language, t

logger = logging.getLogger(__name__)


@rate_limiter
@admin_required
async def deposits_command_handler(client: Client, message: Message):
    """Handle /deposits admin command."""
    try:
        parts = message.text.split()
        
        if len(parts) == 1:
            # Show global deposits statistics
            await show_global_deposits_stats(message)
        elif len(parts) == 2:
            # Show specific user deposits
            try:
                user_id = int(parts[1])
                await show_user_deposits(message, user_id)
            except ValueError:
                await message.reply_text("❌ Invalid user ID. Use: /deposits [user_id]")
        else:
            await message.reply_text("ℹ️ Usage:\n/deposits - Global stats\n/deposits <user_id> - User deposits")
            
    except Exception as e:
        logger.error(f"Error in deposits command: {e}")
        await message.reply_text("❌ An error occurred while fetching deposits data")


async def show_global_deposits_stats(message: Message):
    """Show global deposits statistics."""
    try:
        stats = await user_deposits_repo.get_all_users_deposits_stats()
        
        if not stats:
            await message.reply_text("📊 **Global Deposits Statistics**\n\nNo deposits data available.")
            return
        
        stats_text = "📊 **Global Deposits Statistics**\n\n"
        stats_text += f"👥 **Users with Deposits:** {stats.get('total_users_with_deposits', 0)}\n"
        stats_text += f"📈 **Total Deposits:** {stats.get('total_deposits_count', 0)}\n"
        stats_text += f"💰 **Total Volume:** {stats.get('total_volume', '0.00 USDT')}\n"
        stats_text += f"💸 **Total Fees Collected:** {stats.get('total_fees', '0.00 USDT')}\n"
        stats_text += f"📊 **Avg Deposits/User:** {stats.get('avg_deposits_per_user', '0.0')}\n"
        stats_text += f"💳 **Avg Amount/User:** {stats.get('avg_amount_per_user', '0.00 USDT')}\n"
        
        await message.reply_text(stats_text)
        
    except Exception as e:
        logger.error(f"Error showing global deposits stats: {e}")
        await message.reply_text("❌ Error fetching global deposits statistics")


async def show_user_deposits(message: Message, user_id: int):
    """Show specific user deposits information."""
    try:
        # Get user info
        user = await user_repo.get_by_tg_id(user_id)
        if not user:
            await message.reply_text(f"❌ User with ID {user_id} not found")
            return
        
        # Get deposits summary
        summary = await user_deposits_repo.get_user_deposit_summary(user_id)
        
        if summary['total_deposits'] == 0:
            await message.reply_text(f"📊 **Deposits for {user.first_name} (ID: {user_id})**\n\nNo deposits found.")
            return
        
        deposits_text = f"📊 **Deposits for {user.first_name} (ID: {user_id})**\n\n"
        deposits_text += f"📈 **Total Deposits:** {summary['total_deposits']}\n"
        deposits_text += f"💰 **Total Amount:** {summary['total_amount']}\n"
        deposits_text += f"💸 **Total Fees:** {summary['total_fees']}\n"
        deposits_text += f"🏆 **Largest Deposit:** {summary['largest_deposit']}\n"
        
        if summary['first_deposit']:
            deposits_text += f"🗓️ **First Deposit:** {summary['first_deposit'][:10]}\n"
        if summary['last_deposit']:
            deposits_text += f"📅 **Last Deposit:** {summary['last_deposit'][:10]}\n"
        
        # Assets breakdown
        if summary.get('assets_breakdown'):
            deposits_text += f"\n💎 **Assets Breakdown:**\n"
            for asset, amount in summary['assets_breakdown'].items():
                deposits_text += f"• {amount}\n"
        
        # Recent transactions
        if summary.get('recent_transactions'):
            deposits_text += f"\n📋 **Recent Transactions:**\n"
            for tx in summary['recent_transactions'][:3]:  # Show only 3 most recent
                deposits_text += f"• Invoice {tx['invoice_id']}: {tx['amount']} ({tx['date'][:10]})\n"
                if tx['fee'] != "0.00":
                    deposits_text += f"  Fee: {tx['fee']}\n"
        
        await message.reply_text(deposits_text)
        
    except Exception as e:
        logger.error(f"Error showing user deposits for {user_id}: {e}")
        await message.reply_text(f"❌ Error fetching deposits for user {user_id}")


@rate_limiter
async def user_deposits_callback(client: Client, callback_query: CallbackQuery):
    """Handle user deposits callback for showing personal deposits."""
    try:
        user_id = callback_query.from_user.id
        user = await user_repo.get_by_tg_id(user_id)
        lang = get_user_language(user)
        
        # Get user's deposits summary
        summary = await user_deposits_repo.get_user_deposit_summary(user_id)
        
        if summary['total_deposits'] == 0:
            await callback_query.edit_message_text(
                "💰 **My Deposits**\n\n"
                "You haven't made any deposits yet.\n"
                "Use 💳 Crypto Deposit to add funds to your wallet!"
            )
            return
        
        deposits_text = "💰 **My Deposits**\n\n"
        deposits_text += f"📊 **Summary:**\n"
        deposits_text += f"• Total Deposits: {summary['total_deposits']}\n"
        deposits_text += f"• Total Amount: {summary['total_amount']}\n"
        deposits_text += f"• Total Fees: {summary['total_fees']}\n"
        deposits_text += f"• Largest Deposit: {summary['largest_deposit']}\n"
        
        if summary.get('recent_transactions'):
            deposits_text += f"\n📋 **Recent Deposits:**\n"
            for tx in summary['recent_transactions'][:5]:
                deposits_text += f"• {tx['amount']} on {tx['date'][:10]}\n"
        
        deposits_text += f"\n💡 Tip: Use /balance to check your current wallet balance"
        
        await callback_query.edit_message_text(deposits_text)
        
    except Exception as e:
        logger.error(f"Error in user deposits callback: {e}")
        await callback_query.answer("❌ An error occurred")
