"""Admin keyboards."""

from typing import List
from pyrogram.types import InlineKeyboardMarkup
from .base import BaseKeyboardBuilder
from app.models import Product, Order, User
from app.i18n import _, get_user_language


def get_admin_main_keyboard(user=None) -> InlineKeyboardMarkup:
    """Get admin main menu keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    # First row
    builder.add_buttons_row([
        {"text": _("admin.products", lang), "callback_data": "admin_products"},
        {"text": _("admin.orders", lang), "callback_data": "admin_orders"}
    ])
    
    # Second row
    builder.add_buttons_row([
        {"text": _("admin.users", lang), "callback_data": "admin_users"},
        {"text": _("admin.settings", lang), "callback_data": "admin_settings"}
    ])
    
    # Third row
    builder.add_buttons_row([
        {"text": _("admin.announcements", lang), "callback_data": "admin_announcements"},
        {"text": _("admin.metrics", lang), "callback_data": "admin_metrics"}
    ])
    
    # Fourth row - Revenue Analytics
    builder.add_buttons_row([
        {"text": "💰 Revenue Analytics", "callback_data": "admin_revenue"},
        {"text": "📈 Business Reports", "callback_data": "admin_reports"}
    ])
    
    builder.add_back_button("close_admin")
    
    return builder.build()


def get_admin_products_keyboard(user=None) -> InlineKeyboardMarkup:
    """Get admin products management keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    builder.add_button("➕ Add Product", "admin_add_product")
    builder.add_button("📋 List Products", "admin_list_products")
    builder.add_button("💰 Bulk Update Prices", "admin_bulk_prices")
    builder.add_button("📦 Update Stock", "admin_update_stock")
    builder.add_button("📤 Export Products", "admin_export_products")
    builder.add_button("📥 Import Products", "admin_import_products")
    
    builder.add_back_button("admin_main")
    
    return builder.build()


def get_product_actions_keyboard(product_id: str, user=None) -> InlineKeyboardMarkup:
    """Get product actions keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    builder.add_buttons_row([
        {"text": _("common.edit", lang), "callback_data": f"admin_edit_product:{product_id}"},
        {"text": "📦 Stock", "callback_data": f"admin_product_stock:{product_id}"}
    ])
    
    builder.add_buttons_row([
        {"text": "🔄 Toggle Active", "callback_data": f"admin_toggle_product:{product_id}"},
        {"text": _("common.delete", lang), "callback_data": f"admin_delete_product:{product_id}"}
    ])
    
    builder.add_back_button("admin_list_products")
    
    return builder.build()


def get_admin_orders_keyboard(user=None) -> InlineKeyboardMarkup:
    """Get admin orders management keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    builder.add_button("📋 All Orders", "admin_orders_all")
    builder.add_button("⏳ Pending Orders", "admin_orders_pending")
    builder.add_button("✅ Recent Orders", "admin_orders_recent")
    builder.add_button("📊 Order Stats", "admin_order_stats")
    
    builder.add_back_button("admin_main")
    
    return builder.build()


def get_order_actions_keyboard(order_id: str, user=None) -> InlineKeyboardMarkup:
    """Get order actions keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    builder.add_buttons_row([
        {"text": "✅ Confirm", "callback_data": f"admin_confirm_order:{order_id}"},
        {"text": "🚚 Ship", "callback_data": f"admin_ship_order:{order_id}"}
    ])
    
    builder.add_buttons_row([
        {"text": "💰 Refund", "callback_data": f"admin_refund_order:{order_id}"},
        {"text": "❌ Cancel", "callback_data": f"admin_cancel_order:{order_id}"}
    ])
    
    builder.add_back_button("admin_orders")
    
    return builder.build()


def get_admin_users_keyboard(user=None) -> InlineKeyboardMarkup:
    """Get admin users management keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    builder.add_button("👥 All Users", "admin_users_all")
    builder.add_button("🚫 Banned Users", "admin_users_banned")
    builder.add_button("👑 Admins", "admin_users_admins")
    builder.add_button("📊 User Stats", "admin_user_stats")
    
    builder.add_back_button("admin_main")
    
    return builder.build()


def get_user_actions_keyboard(user_id: int, user=None) -> InlineKeyboardMarkup:
    """Get user actions keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    builder.add_buttons_row([
        {"text": "💰 Adjust Balance", "callback_data": f"admin_adjust_balance:{user_id}"},
        {"text": "👑 Manage Roles", "callback_data": f"admin_manage_roles:{user_id}"}
    ])
    
    builder.add_buttons_row([
        {"text": "🚫 Ban User", "callback_data": f"admin_ban_user:{user_id}"},
        {"text": "✅ Unban User", "callback_data": f"admin_unban_user:{user_id}"}
    ])
    
    builder.add_back_button("admin_users")
    
    return builder.build()


def get_admin_announcements_keyboard(user=None) -> InlineKeyboardMarkup:
    """Get admin announcements keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    builder.add_button("📢 Send Broadcast", "admin_send_broadcast")
    builder.add_button("📅 Schedule Message", "admin_schedule_message")
    builder.add_button("📋 View Scheduled", "admin_view_scheduled")
    builder.add_button("📊 Announcement Stats", "admin_announcement_stats")
    
    builder.add_back_button("admin_main")
    
    return builder.build()


def get_admin_settings_keyboard(user=None) -> InlineKeyboardMarkup:
    """Get admin settings keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    builder.add_button("💬 Support Handle", "admin_support_handle")
    builder.add_button("📝 Text Templates", "admin_text_templates")
    builder.add_button("📅 Daily Message", "admin_daily_message")
    builder.add_button("⚙️ Bot Settings", "admin_bot_settings")
    
    builder.add_back_button("admin_main")
    
    return builder.build()


def get_admin_revenue_keyboard(user=None) -> InlineKeyboardMarkup:
    """Get admin revenue analytics keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    # Time period buttons
    builder.add_buttons_row([
        {"text": "📅 Today", "callback_data": "admin_revenue_today"},
        {"text": "📅 This Week", "callback_data": "admin_revenue_week"}
    ])
    
    builder.add_buttons_row([
        {"text": "📅 This Month", "callback_data": "admin_revenue_month"},
        {"text": "📅 Last 30 Days", "callback_data": "admin_revenue_30days"}
    ])
    
    builder.add_buttons_row([
        {"text": "💰 Top Products", "callback_data": "admin_top_products"},
        {"text": "🏆 Top Customers", "callback_data": "admin_top_customers"}
    ])
    
    builder.add_buttons_row([
        {"text": "📊 Sales Trends", "callback_data": "admin_sales_trends"},
        {"text": "📈 Growth Analysis", "callback_data": "admin_growth_analysis"}
    ])
    
    builder.add_back_button("admin_main")
    
    return builder.build()


def get_admin_reports_keyboard(user=None) -> InlineKeyboardMarkup:
    """Get admin business reports keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    builder.add_buttons_row([
        {"text": "📋 Order Report", "callback_data": "admin_report_orders"},
        {"text": "👥 User Report", "callback_data": "admin_report_users"}
    ])
    
    builder.add_buttons_row([
        {"text": "📦 Inventory Report", "callback_data": "admin_report_inventory"},
        {"text": "💰 Financial Report", "callback_data": "admin_report_financial"}
    ])
    
    builder.add_buttons_row([
        {"text": "📊 Performance Report", "callback_data": "admin_report_performance"},
        {"text": "🎯 Marketing Report", "callback_data": "admin_report_marketing"}
    ])
    
    builder.add_buttons_row([
        {"text": "📤 Export All Data", "callback_data": "admin_export_all"},
        {"text": "📧 Email Reports", "callback_data": "admin_email_reports"}
    ])
    
    builder.add_back_button("admin_main")
    
    return builder.build()

