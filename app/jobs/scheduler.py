"""Job scheduler for automated tasks."""

import asyncio
import logging
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.asyncio import AsyncIOExecutor

from app.config import settings

logger = logging.getLogger(__name__)

# Configure scheduler
executors = {
    'default': AsyncIOExecutor(),
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

scheduler = AsyncIOScheduler(
    executors=executors,
    job_defaults=job_defaults,
    timezone='UTC'
)


async def send_daily_message():
    """Send daily message to main group/channel."""
    try:
        logger.info("Sending daily message...")
        
        # Get settings from database
        from app.db.database import db
        settings_doc = await db.db.settings.find_one({"key": "daily_message_text"})
        
        message_text = "🛍️ Check out our daily deals! Use /start to browse products."
        if settings_doc:
            message_text = settings_doc.get("value", message_text)
        
        # Get active bot clients
        from app.bot import bot
        if not bot.active_clients:
            logger.warning("No active bot clients for daily message")
            return
        
        # Send to main group/channel if configured
        if settings.main_group_id:
            try:
                client = bot.active_clients[0]  # Use first available client
                await client.send_message(settings.main_group_id, message_text)
                logger.info(f"Daily message sent to group {settings.main_group_id}")
            except Exception as e:
                logger.error(f"Failed to send daily message to group: {e}")
        
        if settings.main_channel_id and settings.main_channel_id != settings.main_group_id:
            try:
                client = bot.active_clients[0]
                await client.send_message(settings.main_channel_id, message_text)
                logger.info(f"Daily message sent to channel {settings.main_channel_id}")
            except Exception as e:
                logger.error(f"Failed to send daily message to channel: {e}")
    
    except Exception as e:
        logger.error(f"Error in daily message job: {e}")


async def cleanup_expired_deposits():
    """Clean up expired deposits."""
    try:
        logger.debug("Running deposit cleanup job...")
        from app.services.payment_service import payment_service
        await payment_service.cleanup_expired_deposits()
    except Exception as e:
        logger.error(f"Error in deposit cleanup job: {e}")


async def send_restock_notification(product_name: str, city: str, area: str):
    """Send restock notification to main group."""
    try:
        message = f"🔄 **Restock Alert!**\n\n"
        message += f"📦 {product_name}\n"
        message += f"📍 {city}, {area}\n\n"
        message += f"Use /start to order now!"
        
        from app.bot import bot
        if bot.active_clients and settings.main_group_id:
            client = bot.active_clients[0]
            await client.send_message(settings.main_group_id, message)
            logger.info(f"Restock notification sent for {product_name}")
    
    except Exception as e:
        logger.error(f"Error sending restock notification: {e}")


async def send_new_product_notification(product_name: str, city: str, area: str, price: float):
    """Send new product notification to main group."""
    try:
        message = f"🆕 **New Product Available!**\n\n"
        message += f"🛒 {product_name}\n"
        message += f"💰 {price:.2f} EUR\n"
        message += f"📍 {city}, {area}\n\n"
        message += f"Use /start to order now!"
        
        from app.bot import bot
        if bot.active_clients and settings.main_group_id:
            client = bot.active_clients[0]
            await client.send_message(settings.main_group_id, message)
            logger.info(f"New product notification sent for {product_name}")
    
    except Exception as e:
        logger.error(f"Error sending new product notification: {e}")


async def send_broadcast_message(message_text: str, photo_url: str = None):
    """Send broadcast message to all users."""
    try:
        logger.info("Starting broadcast message...")
        
        from app.db.user_repository import user_repo
        from app.bot import bot
        
        if not bot.active_clients:
            logger.warning("No active bot clients for broadcast")
            return
        
        client = bot.active_clients[0]
        
        # Get all non-banned users
        users = await user_repo.get_many({"is_banned": {"$ne": True}})
        
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                if photo_url:
                    await client.send_photo(user.tg_id, photo_url, caption=message_text)
                else:
                    await client.send_message(user.tg_id, message_text)
                
                sent_count += 1
                
                # Add small delay to avoid rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Failed to send broadcast to user {user.tg_id}: {e}")
                failed_count += 1
        
        logger.info(f"Broadcast complete: {sent_count} sent, {failed_count} failed")
        
        # Send summary to admins
        summary = f"📢 **Broadcast Summary**\n\n"
        summary += f"✅ Sent: {sent_count}\n"
        summary += f"❌ Failed: {failed_count}\n"
        summary += f"📊 Total: {sent_count + failed_count}"
        
        for admin_id in settings.all_admin_ids:
            try:
                await client.send_message(admin_id, summary)
            except:
                pass  # Ignore errors when sending to admins
    
    except Exception as e:
        logger.error(f"Error in broadcast job: {e}")


async def check_inactive_users():
    """Check for inactive users and send balance reminders."""
    try:
        from app.services.inactive_user_service import inactive_user_service
        from app.bot import bot
        
        if not bot.active_clients:
            logger.warning("⚠️ No active bot clients for inactive user check")
            return
            
        # Use the first available bot client
        client = bot.active_clients[0]
        
        # Run the inactive user check
        await inactive_user_service.check_and_notify_inactive_users(client)
        
    except Exception as e:
        logger.error(f"❌ Error in check_inactive_users job: {e}")


def setup_scheduled_jobs():
    """Set up all scheduled jobs."""
    try:
        # Daily message job (9 AM UTC)
        scheduler.add_job(
            send_daily_message,
            CronTrigger(hour=9, minute=0),
            id='daily_message',
            replace_existing=True
        )
        
        # Cleanup job (every hour)
        scheduler.add_job(
            cleanup_expired_deposits,
            CronTrigger(minute=0),
            id='cleanup_deposits',
            replace_existing=True
        )
        
        # Inactive user check job (every minute)
        scheduler.add_job(
            check_inactive_users,
            CronTrigger(second=0),  # Every minute at :00 seconds
            id='check_inactive_users',
            replace_existing=True
        )
        
        logger.info("Scheduled jobs set up successfully")
        
    except Exception as e:
        logger.error(f"Error setting up scheduled jobs: {e}")


def schedule_announcement(message_text: str, scheduled_time: datetime, photo_url: str = None):
    """Schedule a one-time announcement."""
    try:
        job_id = f"announcement_{scheduled_time.timestamp()}"
        
        scheduler.add_job(
            send_broadcast_message,
            'date',
            run_date=scheduled_time,
            args=[message_text, photo_url],
            id=job_id,
            replace_existing=True
        )
        
        logger.info(f"Scheduled announcement for {scheduled_time}")
        return job_id
        
    except Exception as e:
        logger.error(f"Error scheduling announcement: {e}")
        return None


def cancel_scheduled_job(job_id: str) -> bool:
    """Cancel a scheduled job."""
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Cancelled job {job_id}")
        return True
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        return False


# Set up jobs when module is imported
setup_scheduled_jobs()






