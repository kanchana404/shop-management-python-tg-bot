"""Handlers module."""

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from .user_handlers import (
    start_handler,
    main_menu_callback,
    city_selection_callback,
    area_selection_callback,
    add_to_cart_callback,
    checkout_callback,
    language_callback
)
from .crypto_payment_handlers import (
    crypto_deposit_callback,
    crypto_asset_selection_callback,
    crypto_deposit_amount_handler,
    crypto_payment_callback,
    crypto_balance_callback,
    crypto_rates_callback
)
from .admin_handlers import (
    admin_command_handler,
    admin_main_callback,
    admin_products_callback,
    admin_orders_callback,
    admin_users_callback,
    admin_revenue_callback,
    admin_reports_callback,
    admin_announcements_callback,
    admin_back_callback,
    addproduct_command_handler,
    bulkprice_command_handler,
    updatestock_command_handler,
    broadcast_command_handler
)

import logging

logger = logging.getLogger(__name__)

async def global_debug_callback(client, callback_query):
    """Global debug handler to log ALL callbacks."""
    try:
        user_id = callback_query.from_user.id
        username = callback_query.from_user.username or "No username"
        first_name = callback_query.from_user.first_name or "No name"
        
        print(f"\n📱 BUTTON CLICKED:")
        print(f"   User: {first_name} (@{username}) - ID: {user_id}")
        print(f"   Button Data: '{callback_query.data}'")
        print(f"   Message: {callback_query.message.text[:50]}...")
        print(f"   ID: {callback_query.id}")
        print("   🔄 Looking for handler...\n")
    except Exception as e:
        print(f"Debug handler error: {e}")
    
    # IMPORTANT: Raise StopPropagation(False) to continue to other handlers
    from pyrogram.errors import StopPropagation
    raise StopPropagation(False)

async def debug_unhandled_callback(client, callback_query):
    """Debug handler for unhandled callbacks."""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "No username"
    first_name = callback_query.from_user.first_name or "No name"
    
    print(f"\n🔍 BUTTON PRESSED DEBUG:")
    print(f"   User: {first_name} (@{username}) - ID: {user_id}")
    print(f"   Button Data: '{callback_query.data}'")
    print(f"   Message Text: {callback_query.message.text[:100]}...")
    print(f"   ⚠️  UNHANDLED - No handler matched this callback\n")
    
    logger.warning(f"UNHANDLED CALLBACK: {callback_query.data} from user {user_id}")
    await callback_query.answer("Debug: Unhandled callback")


def register_user_handlers(app: Client):
    """Register user handlers."""
    
    # Command handlers
    app.add_handler(MessageHandler(start_handler, filters.command("start")))
    
    # Callback handlers for main menu and navigation
    app.add_handler(CallbackQueryHandler(main_menu_callback, filters.regex(r"^(order_products|check_stock|support|language|my_cart|back_to_main|back_to_products|back_to_cities)$")))
    
    # Back to area callback (with city parameter)
    app.add_handler(CallbackQueryHandler(main_menu_callback, filters.regex(r"^back_to_area:")))
    
    # Location selection
    app.add_handler(CallbackQueryHandler(city_selection_callback, filters.regex(r"^city:")))
    app.add_handler(CallbackQueryHandler(area_selection_callback, filters.regex(r"^area:")))
    
    # Product actions
    app.add_handler(CallbackQueryHandler(add_to_cart_callback, filters.regex(r"^add_to_cart:")))
    app.add_handler(CallbackQueryHandler(checkout_callback, filters.regex(r"^checkout$")))
    
    # Language selection
    app.add_handler(CallbackQueryHandler(language_callback, filters.regex(r"^lang:")))
    
    # Crypto payment handlers
    app.add_handler(CallbackQueryHandler(crypto_deposit_callback, filters.regex(r"^crypto_deposit$")))
    app.add_handler(CallbackQueryHandler(crypto_asset_selection_callback, filters.regex(r"^crypto_asset:")))
    app.add_handler(CallbackQueryHandler(crypto_payment_callback, filters.regex(r"^crypto_pay:")))
    app.add_handler(CallbackQueryHandler(crypto_balance_callback, filters.regex(r"^crypto_balance$")))
    app.add_handler(CallbackQueryHandler(crypto_rates_callback, filters.regex(r"^crypto_rates$")))
    
    # Message handlers for amount input (only for crypto deposit replies)
    app.add_handler(MessageHandler(crypto_deposit_amount_handler, filters.text))
    
    # Debug handler for unhandled callbacks (should be last)
    app.add_handler(CallbackQueryHandler(debug_unhandled_callback, filters.regex(r".*")))


def register_admin_handlers(app: Client):
    """Register admin handlers."""
    
    # Admin command
    app.add_handler(MessageHandler(admin_command_handler, filters.command("admin")))
    
    # Product management commands
    app.add_handler(MessageHandler(addproduct_command_handler, filters.command("addproduct")))
    app.add_handler(MessageHandler(bulkprice_command_handler, filters.command("bulkprice")))
    app.add_handler(MessageHandler(updatestock_command_handler, filters.command("updatestock")))
    
    # Announcement commands
    app.add_handler(MessageHandler(broadcast_command_handler, filters.command("broadcast")))
    
    # Admin main menu callbacks
    app.add_handler(CallbackQueryHandler(admin_main_callback, filters.regex(r"^(admin_products|admin_orders|admin_users|admin_announcements|admin_settings|admin_metrics|admin_revenue|admin_reports|admin_main|close_admin)$")))
    
    # Admin submenu callbacks
    app.add_handler(CallbackQueryHandler(admin_products_callback, filters.regex(r"^admin_(add_product|list_products|bulk_prices|update_stock|export_products|import_products)$")))
    app.add_handler(CallbackQueryHandler(admin_orders_callback, filters.regex(r"^admin_orders_(all|pending|recent)|admin_order_stats$")))
    app.add_handler(CallbackQueryHandler(admin_users_callback, filters.regex(r"^admin_users_(all|banned|admins)|admin_user_stats$")))
    
    # Announcement callbacks
    app.add_handler(CallbackQueryHandler(admin_announcements_callback, filters.regex(r"^admin_(send_broadcast|schedule_message|view_scheduled|announcement_stats)$")))
    
    # Revenue analytics callbacks
    app.add_handler(CallbackQueryHandler(admin_revenue_callback, filters.regex(r"^admin_revenue_(today|week|month|30days)|admin_(top_products|top_customers|sales_trends|growth_analysis)$")))
    
    # Reports callbacks (specific reports first, then back navigation)
    app.add_handler(CallbackQueryHandler(admin_reports_callback, filters.regex(r"^admin_report_(orders|users|inventory|financial|performance|marketing)|admin_(export_all|email_reports)$")))
    
    # Back navigation
    app.add_handler(CallbackQueryHandler(admin_back_callback, filters.regex(r"^admin_main_back$")))


def register_all_handlers(app: Client):
    """Register all handlers."""
    # Register admin handlers FIRST (commands should be processed before general text handlers)
    register_admin_handlers(app)
    register_user_handlers(app)
    # TODO: Add payment handlers, etc.


__all__ = ["register_all_handlers"]
