#!/usr/bin/env python3
"""
Main entry point for the Telegram Shop Bot.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add app to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.bot import run_bot


def setup_logging():
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    log_path = Path(settings.log_file).parent
    log_path.mkdir(exist_ok=True)
    
    # Configure logging with UTF-8 encoding
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(settings.log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set console encoding for Windows
    if sys.platform.startswith('win'):
        try:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        except Exception:
            # Fallback: remove emojis from console logs
            pass
    
    # Set specific log levels for noisy libraries
    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


def main():
    """Main function."""
    print("🤖 Starting Telegram Shop Bot...")
    print(f"📊 Environment: {settings.environment}")
    print(f"🤖 Bot tokens configured: {len(settings.bot_tokens)}")
    print(f"🗄️  Database: {settings.database_name}")
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Validate configuration
        if not settings.bot_tokens:
            raise ValueError("No bot tokens configured! Please set BOT_TOKENS environment variable.")
        
        if not settings.owner_id:
            raise ValueError("No owner ID configured! Please set OWNER_ID environment variable.")
        
        logger.info("Configuration validated successfully")
        
        # Run the bot
        asyncio.run(run_bot())
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()








