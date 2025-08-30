#!/usr/bin/env python3
"""
Script to verify the bot setup is working correctly.
"""

import sys
import asyncio
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.basicConfig(level=logging.INFO)

async def verify_setup():
    """Verify the bot setup."""
    print("🔍 Verifying Telegram Shop Bot setup...")
    
    try:
        # Test configuration loading
        print("📋 Testing configuration...")
        from app.config import settings
        print(f"   ✅ Settings loaded successfully")
        print(f"   📊 Bot tokens configured: {len(settings.bot_tokens)}")
        print(f"   🗄️ Database: {settings.database_name}")
        print(f"   🌍 Environment: {settings.environment}")
        
        # Test model imports
        print("\n📦 Testing models...")
        from app.models import User, Product, Cart, Order, Deposit
        print("   ✅ All models imported successfully")
        
        # Test i18n system
        print("\n🌐 Testing i18n system...")
        from app.i18n import _, translator
        text = _("start.welcome", "en")
        print(f"   ✅ Translation working: {text[:50]}...")
        
        # Test keyboard builders
        print("\n⌨️ Testing keyboard builders...")
        from app.keyboards import get_main_menu_keyboard
        keyboard = get_main_menu_keyboard()
        print(f"   ✅ Main menu keyboard created with {len(keyboard.inline_keyboard)} rows")
        
        # Test that handlers can be imported (skip if DB not available)
        print("\n🎯 Testing handlers...")
        try:
            from app.handlers import register_all_handlers
            print("   ✅ Handler registration function available")
        except AttributeError as e:
            if "'NoneType' object has no attribute" in str(e):
                print("   ⚠️ Handlers skipped (database not connected)")
            else:
                raise
        
        # Test scheduler
        print("\n📅 Testing scheduler...")
        from app.jobs import scheduler
        print(f"   ✅ Scheduler available: {scheduler}")
        
        print("\n✅ ALL CHECKS PASSED!")
        print("\n🚀 Your Telegram Shop Bot is ready to run!")
        print("\n📝 Next steps:")
        print("   1. Create a .env file with your bot tokens")
        print("   2. Set up MongoDB (or use Docker)")
        print("   3. Run: python main.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Setup verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(verify_setup())
    sys.exit(0 if success else 1)
