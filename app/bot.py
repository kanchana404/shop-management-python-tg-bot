"""Main bot application with multi-bot support."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import List
from pyrogram import Client
from pyrogram.errors import FloodWait, ApiIdInvalid, AuthKeyUnregistered

from app.config import settings
from app.db import db
from app.handlers import register_all_handlers
from app.jobs.scheduler import scheduler
from app.utils.rate_limiter import cleanup_old_requests
from app.db.user_repository import user_repo

logger = logging.getLogger(__name__)


class TelegramShopBot:
    """Main bot class with multi-bot support."""
    
    def __init__(self):
        self.clients: List[Client] = []
        self.active_clients: List[Client] = []
        self.is_running = False
    
    def _ensure_session_directory(self):
        """Ensure session directory exists and is writable."""
        try:
            # Try to create the configured session directory
            session_path = Path(settings.session_dir)
            session_path.mkdir(parents=True, exist_ok=True)
            
            # Test write access
            test_file = session_path / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            
            logger.info(f"✅ Session directory ready: {session_path.absolute()}")
            return str(session_path)
            
        except (PermissionError, OSError) as e:
            logger.warning(f"⚠️ Cannot write to {settings.session_dir}: {e}")
            
            # Fallback to temporary directory
            try:
                temp_session_dir = Path(tempfile.gettempdir()) / "telegram_bot_sessions"
                temp_session_dir.mkdir(parents=True, exist_ok=True)
                
                # Test write access
                test_file = temp_session_dir / ".write_test"
                test_file.write_text("test")
                test_file.unlink()
                
                logger.info(f"✅ Using temp session directory: {temp_session_dir.absolute()}")
                return str(temp_session_dir)
                
            except (PermissionError, OSError) as temp_e:
                logger.warning(f"⚠️ Cannot write to temp directory: {temp_e}")
                
                # Final fallback to current directory
                current_dir = Path.cwd() / ".sessions"
                current_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Using current directory for sessions: {current_dir.absolute()}")
                return str(current_dir)

    async def initialize(self):
        """Initialize bot clients and database."""
        logger.info("Initializing Telegram Shop Bot...")
        
        # Connect to database
        await db.connect()
        
        # Ensure session directory exists and is writable
        session_dir = self._ensure_session_directory()
        
        # Create bot clients
        for i, token in enumerate(settings.bot_tokens):
            try:
                client = Client(
                    name=f"bot_{i}",
                    bot_token=token,
                    api_id=settings.api_id,
                    api_hash=settings.api_hash,
                    workdir=session_dir
                )
                
                # Register handlers for this client
                register_all_handlers(client)
                
                self.clients.append(client)
                logger.info(f"Created bot client {i}")
                
            except Exception as e:
                logger.error(f"Failed to create bot client {i}: {e}")
        
        if not self.clients:
            raise RuntimeError("No valid bot clients created!")
        
        logger.info(f"Initialized {len(self.clients)} bot clients")
    
    async def start(self):
        """Start all bot clients."""
        if self.is_running:
            logger.warning("Bot is already running")
            return
        
        logger.info("Starting bot clients...")
        
        # Start each client
        for i, client in enumerate(self.clients):
            try:
                await client.start()
                self.active_clients.append(client)
                
                # Get bot info
                me = await client.get_me()
                logger.info(f"Bot {i} started: @{me.username} ({me.id})")
                
            except (ApiIdInvalid, AuthKeyUnregistered) as e:
                logger.error(f"Bot {i} authentication failed: {e}")
            except FloodWait as e:
                logger.warning(f"Bot {i} flood wait: {e.value} seconds")
                await asyncio.sleep(e.value)
                try:
                    await client.start()
                    self.active_clients.append(client)
                except Exception as retry_e:
                    logger.error(f"Bot {i} failed after flood wait: {retry_e}")
            except Exception as e:
                logger.error(f"Failed to start bot {i}: {e}")
        
        if not self.active_clients:
            raise RuntimeError("No bot clients started successfully!")
        
        self.is_running = True
        logger.info(f"Started {len(self.active_clients)} out of {len(self.clients)} bot clients")
        
        # Start scheduler
        if not scheduler.running:
            scheduler.start()
            logger.info("Scheduler started")
        
        # Start background tasks
        asyncio.create_task(self._background_tasks())
        
        # Send admin notification
        await self._send_admin_startup_notification()
    
    async def stop(self):
        """Stop all bot clients."""
        if not self.is_running:
            return
        
        logger.info("Stopping bot clients...")
        
        # Stop scheduler
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Scheduler stopped")
        
        # Stop all clients
        for i, client in enumerate(self.active_clients):
            try:
                await client.stop()
                logger.info(f"Bot {i} stopped")
            except Exception as e:
                logger.error(f"Error stopping bot {i}: {e}")
        
        # Disconnect from database
        await db.disconnect()
        
        self.active_clients.clear()
        self.is_running = False
        logger.info("Bot stopped")
    
    async def _background_tasks(self):
        """Run background maintenance tasks."""
        while self.is_running:
            try:
                # Clean up rate limiter every 5 minutes
                cleanup_old_requests()
                
                # Clean up expired deposits
                from app.services.payment_service import payment_service
                await payment_service.cleanup_expired_deposits()
                
                # Wait 5 minutes before next cleanup
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in background tasks: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def restart_failed_clients(self):
        """Restart any failed clients."""
        if not self.is_running:
            return
        
        logger.info("Checking for failed clients...")
        
        failed_clients = []
        for i, client in enumerate(self.active_clients):
            try:
                # Try to get bot info to check if client is still active
                await client.get_me()
            except Exception as e:
                logger.warning(f"Bot {i} appears to be failed: {e}")
                failed_clients.append((i, client))
        
        # Restart failed clients
        for i, client in failed_clients:
            try:
                self.active_clients.remove(client)
                await client.stop()
                await asyncio.sleep(5)
                await client.start()
                self.active_clients.append(client)
                logger.info(f"Restarted bot {i}")
            except Exception as e:
                logger.error(f"Failed to restart bot {i}: {e}")
    
    async def _send_admin_startup_notification(self):
        """Send startup notification to all admins."""
        if not self.active_clients:
            return
        
        try:
            # Get admin users from database
            admin_users = await user_repo.get_admins()
            admin_ids_from_db = [user.tg_id for user in admin_users]
            
            # Combine with config admin IDs
            all_admin_ids = list(set(settings.all_admin_ids + admin_ids_from_db))
            
            if not all_admin_ids:
                logger.info("No admin IDs configured - skipping admin notification")
                return
            
            # Create startup message
            if settings.admin_startup_message:
                # Use custom message with basic substitutions
                startup_message = settings.admin_startup_message.format(
                    active_clients=len(self.active_clients),
                    total_clients=len(self.clients),
                    environment=settings.environment,
                    scheduler_status='Running' if scheduler.running else 'Stopped'
                )
            else:
                # Use default message
                startup_message = (
                    "🤖 **Bot Started Successfully!**\n\n"
                    f"✅ **Active Clients:** {len(self.active_clients)}/{len(self.clients)}\n"
                    f"📊 **Environment:** {settings.environment}\n"
                    f"🗄️ **Database:** Connected\n"
                    f"⏰ **Scheduler:** {'Running' if scheduler.running else 'Stopped'}\n"
                    f"🔧 **Admin Panel:** Available via /admin\n\n"
                    f"**Bot Status:** Ready for operations! 🚀"
                )
            
            # Send to all admins using the first available client
            client = self.active_clients[0]
            successful_sends = 0
            
            for admin_id in all_admin_ids:
                try:
                    await client.send_message(admin_id, startup_message)
                    successful_sends += 1
                    logger.info(f"Startup notification sent to admin {admin_id}")
                    await asyncio.sleep(0.5)  # Small delay to avoid rate limits
                except Exception as e:
                    logger.warning(f"Failed to send startup notification to admin {admin_id}: {e}")
            
            logger.info(f"Startup notifications sent to {successful_sends}/{len(all_admin_ids)} admins")
            
        except Exception as e:
            logger.error(f"Error sending admin startup notifications: {e}")

    def get_health_status(self) -> dict:
        """Get health status of all bots."""
        return {
            "total_clients": len(self.clients),
            "active_clients": len(self.active_clients),
            "is_running": self.is_running,
            "scheduler_running": scheduler.running if scheduler else False
        }


# Global bot instance
bot = TelegramShopBot()


async def run_bot():
    """Run the bot application."""
    try:
        await bot.initialize()
        await bot.start()
        
        logger.info("Bot is running. Press Ctrl+C to stop.")
        
        # Keep the bot running
        while bot.is_running:
            await asyncio.sleep(1)
            
            # Periodically check and restart failed clients
            if asyncio.get_event_loop().time() % 300 < 1:  # Every 5 minutes
                await bot.restart_failed_clients()
    
    except KeyboardInterrupt:
        logger.info("Received stop signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await bot.stop()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(settings.log_file),
            logging.StreamHandler()
        ]
    )
    
    # Run the bot
    asyncio.run(run_bot())
