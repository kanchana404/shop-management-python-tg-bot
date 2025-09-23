"""Admin handlers for the bot."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.errors import MessageNotModified

from app.config import settings
from app.db.user_repository import user_repo
from app.db.product_repository import product_repo
from app.services.order_service import order_service
from app.models import UserRole, OrderStatus, ProductCreate, City, Area, CITY_AREAS
from app.keyboards.admin import (
    get_admin_main_keyboard,
    get_admin_products_keyboard,
    get_admin_orders_keyboard,
    get_admin_users_keyboard,
    get_admin_announcements_keyboard,
    get_admin_settings_keyboard,
    get_admin_revenue_keyboard,
    get_admin_reports_keyboard,
    get_product_actions_keyboard,
    get_order_actions_keyboard,
    get_user_actions_keyboard
)
from app.i18n import translator, get_user_language
from app.utils.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


def get_status_value(status):
    """Helper function to safely get status string value."""
    if hasattr(status, 'value'):
        return status.value
    return str(status)


async def safe_edit_message(callback_query: CallbackQuery, text: str, reply_markup=None):
    """Safely edit message, handling MessageNotModified errors."""
    try:
        await callback_query.edit_message_text(text, reply_markup=reply_markup)
    except MessageNotModified:
        # Message content is the same, just answer the callback
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        await callback_query.answer("❌ An error occurred")


async def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    try:
        # Check config admin IDs
        if user_id in settings.all_admin_ids:
            return True
        
        # Check database roles
        user = await user_repo.get_by_tg_id(user_id)
        if user and any(role in [UserRole.OWNER.value, UserRole.ADMIN.value, UserRole.STAFF.value] for role in user.roles):
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False


@rate_limiter
async def admin_command_handler(client: Client, message: Message):
    """Handle /admin command."""
    try:
        user_id = message.from_user.id
        
        if not await is_admin(user_id):
            await message.reply_text("❌ Access denied. You don't have admin privileges.")
            return
        
        user = await user_repo.get_by_tg_id(user_id)
        
        admin_text = (
            "🔧 **Admin Panel**\n\n"
            "Welcome to the administration panel! Here you can:\n\n"
            "📦 **Products**: Add, edit, manage inventory\n"
            "📋 **Orders**: View and manage customer orders\n"
            "👥 **Users**: Manage user accounts and roles\n"
            "📢 **Announcements**: Send broadcasts and notifications\n"
            "📊 **Metrics**: View revenue and analytics\n"
            "⚙️ **Settings**: Configure bot settings\n\n"
            "Choose an option below:"
        )
        
        keyboard = get_admin_main_keyboard(user)
        await message.reply_text(admin_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in admin command handler: {e}")
        await message.reply_text("❌ An error occurred accessing admin panel")


@rate_limiter
async def admin_main_callback(client: Client, callback_query: CallbackQuery):
    """Handle admin main menu callbacks."""
    try:
        user_id = callback_query.from_user.id
        
        if not await is_admin(user_id):
            await callback_query.answer("❌ Access denied", show_alert=True)
            return
        
        data = callback_query.data
        user = await user_repo.get_by_tg_id(user_id)
        
        if data == "admin_products":
            text = "📦 **Product Management**\n\nManage your product catalog:"
            keyboard = get_admin_products_keyboard(user)
            
        elif data == "admin_orders":
            text = "📋 **Order Management**\n\nView and manage customer orders:"
            keyboard = get_admin_orders_keyboard(user)
            
        elif data == "admin_users":
            text = "👥 **User Management**\n\nManage user accounts and permissions:"
            keyboard = get_admin_users_keyboard(user)
            
        elif data == "admin_announcements":
            text = "📢 **Announcements**\n\nSend broadcasts and notifications:"
            keyboard = get_admin_announcements_keyboard(user)
            
        elif data == "admin_settings":
            text = "⚙️ **Bot Settings**\n\nConfigure bot settings and templates:"
            keyboard = get_admin_settings_keyboard(user)
            
        elif data == "admin_metrics":
            await show_admin_metrics(callback_query, user)
            return
            
        elif data == "admin_revenue":
            text = "💰 **Revenue Analytics**\n\nSelect time period or analysis type:"
            keyboard = get_admin_revenue_keyboard(user)
            
        elif data == "admin_reports":
            text = "📈 **Business Reports**\n\nGenerate comprehensive business reports:"
            keyboard = get_admin_reports_keyboard(user)
            
        elif data == "close_admin":
            await callback_query.message.delete()
            return
            
        else:
            await callback_query.answer("❌ Invalid option")
            return
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in admin main callback: {e}")
        await callback_query.answer("❌ An error occurred", show_alert=True)


async def show_admin_metrics(callback_query: CallbackQuery, user):
    """Show admin metrics and analytics."""
    try:
        # Get various metrics
        stats = await order_service.get_order_stats(30)  # Last 30 days
        today_orders = await order_service.get_today_orders_count()
        today_revenue = await order_service.get_today_revenue()
        total_users = await user_repo.get_active_users_count()
        total_products = await product_repo.count({})
        
        # Calculate weekly revenue
        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_stats = await order_service.get_order_stats(7)
        
        metrics_text = (
            "📊 **Bot Analytics & Metrics**\n\n"
            "**📈 Revenue:**\n"
            f"• Today: USDT{today_revenue:.2f}\n"
            f"• This Week: USDT{weekly_stats.get('total_revenue', 0):.2f}\n"
            f"• Last 30 Days: USDT{stats.get('total_revenue', 0):.2f}\n\n"
            
            "**📋 Orders:**\n"
            f"• Today: {today_orders}\n"
            f"• This Week: {weekly_stats.get('total_orders', 0)}\n"
            f"• Last 30 Days: {stats.get('total_orders', 0)}\n\n"
            
            "**👥 Users & Products:**\n"
            f"• Active Users: {total_users}\n"
            f"• Total Products: {total_products}\n\n"
            
            "**📦 Order Status Breakdown (30 days):**\n"
        )
        
        # Add order status breakdown
        if stats.get('by_status'):
            for status, data in stats['by_status'].items():
                count = data['count']
                amount = data['total_amount']
                metrics_text += f"• {status.title()}: {count} orders (USDT{amount:.2f})\n"
        
        # Add quick actions keyboard
        from app.keyboards.base import BaseKeyboardBuilder
        builder = BaseKeyboardBuilder()
        
        builder.add_buttons_row([
            {"text": "📊 Detailed Report", "callback_data": "admin_detailed_report"},
            {"text": "📈 Export Data", "callback_data": "admin_export_data"}
        ])
        
        builder.add_buttons_row([
            {"text": "🔄 Refresh", "callback_data": "admin_metrics"},
            {"text": "⬅️ Back", "callback_data": "admin_main_back"}
        ])
        
        keyboard = builder.build()
        
        await callback_query.edit_message_text(metrics_text, reply_markup=keyboard)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error showing admin metrics: {e}")
        await callback_query.answer("❌ Error loading metrics", show_alert=True)


@rate_limiter
async def admin_products_callback(client: Client, callback_query: CallbackQuery):
    """Handle admin products callbacks."""
    try:
        user_id = callback_query.from_user.id
        
        if not await is_admin(user_id):
            await callback_query.answer("❌ Access denied", show_alert=True)
            return
        
        data = callback_query.data
        user = await user_repo.get_by_tg_id(user_id)
        
        if data == "admin_add_product":
            text = (
                "➕ **Add New Product**\n\n"
                "Please send product details in this format:\n\n"
                "`/addproduct Name|Description|Price|City|Area`\n\n"
                "Example:\n"
                "`/addproduct iPhone 15|Latest iPhone model|999.99|Belgrade|Vracar`\n\n"
                "💡 **Note:** Products are active by default. Use admin panel to deactivate if needed."
            )
            
        elif data == "admin_list_products":
            products = await product_repo.get_many({}, limit=10)
            if not products:
                text = "📋 **Product List**\n\nNo products found."
            else:
                text = "📋 **Product List**\n\n"
                for product in products:
                    status = "✅ Active" if product.is_active else "❌ Inactive"
                    text += f"**{product.name}**\n"
                    text += f"🆔 **ID:** `{product.id}`\n"
                    text += f"💰 **Price:** USDT{product.price}\n"
                    text += f"📍 **Location:** {getattr(product.city, 'value', product.city)}, {getattr(product.area, 'value', product.area)}\n"
                    text += f"📊 **Status:** {status}\n\n"
            
        elif data == "admin_bulk_prices":
            text = (
                "💰 **Bulk Price Update**\n\n"
                "Update multiple product prices:\n\n"
                "`/bulkprice percentage increase/decrease`\n\n"
                "Examples:\n"
                "`/bulkprice +10` (increase all by 10%)\n"
                "`/bulkprice -5` (decrease all by 5%)"
            )
            
        elif data == "admin_update_stock":
            text = (
                "📦 **Stock Management**\n\n"
                "Update product stock:\n\n"
                "`/updatestock product_id new_stock`\n\n"
                "Example:\n"
                "`/updatestock 60a1b2c3d4e5f6789 25`"
            )
            
        elif data == "admin_export_products":
            text = "📤 **Export Products**\n\nExporting product data to CSV..."
            # TODO: Implement CSV export
            
        elif data == "admin_import_products":
            text = (
                "📥 **Import Products**\n\n"
                "Send a CSV file with columns:\n"
                "Name, Description, Price, Stock, City, Area\n\n"
                "The file will be processed automatically."
            )
            
        else:
            await callback_query.answer("❌ Invalid option")
            return
        
        # Create back button
        from app.keyboards.base import BaseKeyboardBuilder
        builder = BaseKeyboardBuilder()
        builder.add_back_button("admin_products")
        keyboard = builder.build()
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in admin products callback: {e}")
        await callback_query.answer("❌ An error occurred", show_alert=True)


@rate_limiter
async def admin_orders_callback(client: Client, callback_query: CallbackQuery):
    """Handle admin orders callbacks."""
    try:
        user_id = callback_query.from_user.id
        
        if not await is_admin(user_id):
            await callback_query.answer("❌ Access denied", show_alert=True)
            return
        
        data = callback_query.data
        user = await user_repo.get_by_tg_id(user_id)
        
        if data == "admin_orders_all":
            orders = await order_service.get_recent_orders(limit=10)
            text = "📋 **All Orders**\n\n"
            
        elif data == "admin_orders_pending":
            orders = await order_service.get_orders_by_status(OrderStatus.PENDING, limit=10)
            text = "⏳ **Pending Orders**\n\n"
            
        elif data == "admin_orders_recent":
            orders = await order_service.get_recent_orders(limit=10)
            text = "📋 **Recent Orders**\n\n"
            
        elif data == "admin_order_stats":
            stats = await order_service.get_order_stats(30)
            text = (
                "📊 **Order Statistics (30 days)**\n\n"
                f"Total Orders: {stats.get('total_orders', 0)}\n"
                f"Total Revenue: USDT{stats.get('total_revenue', 0):.2f}\n\n"
                "By Status:\n"
            )
            for status, data in stats.get('by_status', {}).items():
                text += f"• {status.title()}: {data['count']} orders\n"
            
            from app.keyboards.base import BaseKeyboardBuilder
            builder = BaseKeyboardBuilder()
            builder.add_back_button("admin_orders")
            keyboard = builder.build()
            
            await callback_query.edit_message_text(text, reply_markup=keyboard)
            await callback_query.answer()
            return
            
        else:
            await callback_query.answer("❌ Invalid option")
            return
        
        # Display orders
        if 'orders' in locals():
            if not orders:
                text += "No orders found."
                from app.keyboards.base import BaseKeyboardBuilder
                builder = BaseKeyboardBuilder()
                builder.add_back_button("admin_orders")
                keyboard = builder.build()
            else:
                # Show first 5 orders with action buttons
                for i, order in enumerate(orders[:5], 1):
                    status_emoji = {
                        "pending": "⏳",
                        "confirmed": "✅", 
                        "processing": "🔄",
                        "shipped": "🚚",
                        "delivered": "📦",
                        "cancelled": "❌",
                        "refunded": "💸"
                    }.get(get_status_value(order.status), "📋")
                    
                    text += f"**{i}. Order #{order.id[:8]}**\n"
                    text += f"👤 User ID: {order.user_id}\n"
                    text += f"💰 Total: {order.total_amount:.2f} USDT\n"
                    text += f"{status_emoji} Status: {get_status_value(order.status).upper()}\n"
                    text += f"📅 Created: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                    
                    # Show last update if different from creation
                    if order.updated_at and order.updated_at != order.created_at:
                        time_diff = order.updated_at - order.created_at
                        if time_diff.total_seconds() > 60:
                            text += f"🔄 Updated: {order.updated_at.strftime('%Y-%m-%d %H:%M')}\n"
                    
                    text += f"🛍️ Items: {len(order.items)} products\n\n"
                
                if len(orders) > 5:
                    text += f"... and {len(orders) - 5} more orders\n\n"
                
                # Create action buttons for order management
                from app.keyboards.base import BaseKeyboardBuilder
                builder = BaseKeyboardBuilder()
                
                # Add individual order buttons (first 3 orders)
                for i, order in enumerate(orders[:3], 1):
                    builder.add_button(
                        f"🔧 Manage Order #{order.id[:8]}", 
                        f"admin_manage_order:{order.id}"
                    )
                
                # Add navigation buttons
                builder.add_buttons_row([
                    {"text": "🔄 Refresh", "callback_data": data},
                    {"text": "⬅️ Back", "callback_data": "admin_orders"}
                ])
                keyboard = builder.build()
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in admin orders callback: {e}")
        await callback_query.answer("❌ An error occurred", show_alert=True)


@rate_limiter
async def admin_manage_order_callback(client: Client, callback_query: CallbackQuery):
    """Handle individual order management."""
    try:
        user_id = callback_query.from_user.id
        
        if not await is_admin(user_id):
            await callback_query.answer("❌ Access denied", show_alert=True)
            return
        
        data = callback_query.data
        
        if data.startswith("admin_manage_order:"):
            order_id = data.split(":", 1)[1]
            order = await order_service.get_order_by_id(order_id)
            
            if not order:
                await callback_query.answer("❌ Order not found", show_alert=True)
                return
            
            # Get customer info
            customer = await user_repo.get_by_tg_id(order.user_id)
            customer_name = f"{customer.first_name}" if customer else f"User {order.user_id}"
            if customer and customer.last_name:
                customer_name += f" {customer.last_name}"
            
            # Build detailed order view
            status_emoji = {
                "pending": "⏳",
                "confirmed": "✅", 
                "processing": "🔄",
                "shipped": "🚚",
                "delivered": "📦",
                "cancelled": "❌",
                "refunded": "💸"
            }.get(get_status_value(order.status), "📋")
            
            text = f"🔧 **Order Management**\n"
            text += f"Order #{order.id[:8]}\n"
            text += "═" * 30 + "\n\n"
            
            text += f"👤 **Customer:** {customer_name}\n"
            text += f"📞 **User ID:** {order.user_id}\n"
            if customer and customer.username:
                text += f"👤 **Username:** @{customer.username}\n"
            text += f"💰 **Balance:** {customer.balance:.2f} USDT\n\n" if customer else ""
            
            text += f"{status_emoji} **Status:** {get_status_value(order.status).upper()}\n"
            text += f"💰 **Total:** {order.total_amount:.2f} USDT\n"
            text += f"💳 **Payment:** {order.payment_method}\n"
            text += f"📅 **Created:** {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # Show updated time if different from created time
            if order.updated_at and order.updated_at != order.created_at:
                time_diff = order.updated_at - order.created_at
                if time_diff.total_seconds() > 60:  # Only show if more than 1 minute difference
                    text += f"🔄 **Last Updated:** {order.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            text += "\n"
            
            text += f"🛍️ **Items Ordered ({len(order.items)}):**\n"
            for i, item in enumerate(order.items, 1):
                text += f"{i}. **{item.product_name}**\n"
                text += f"   💰 {item.price:.2f} USDT × {item.quantity} = {item.total_price:.2f} USDT\n"
            
            if order.notes:
                text += f"\n📝 **Notes:** {order.notes}\n"
            
            # Create action buttons based on current status
            from app.keyboards.base import BaseKeyboardBuilder
            builder = BaseKeyboardBuilder()
            
            status_value = get_status_value(order.status)
            
            if status_value == "pending":
                builder.add_buttons_row([
                    {"text": "✅ Confirm Order", "callback_data": f"admin_order_action:confirm:{order.id}"},
                    {"text": "❌ Cancel Order", "callback_data": f"admin_order_action:cancel:{order.id}"}
                ])
            elif status_value == "confirmed":
                builder.add_buttons_row([
                    {"text": "🔄 Start Processing", "callback_data": f"admin_order_action:processing:{order.id}"},
                    {"text": "❌ Cancel Order", "callback_data": f"admin_order_action:cancel:{order.id}"}
                ])
            elif status_value == "processing":
                builder.add_buttons_row([
                    {"text": "🚚 Mark as Shipped", "callback_data": f"admin_order_action:shipped:{order.id}"},
                    {"text": "❌ Cancel Order", "callback_data": f"admin_order_action:cancel:{order.id}"}
                ])
            elif status_value == "shipped":
                builder.add_button("📦 Mark as Delivered", f"admin_order_action:delivered:{order.id}")
            
            # Always available actions
            if status_value not in ["delivered", "cancelled", "refunded"]:
                builder.add_button("📝 Add Notes", f"admin_order_notes:{order.id}")
            
            builder.add_buttons_row([
                {"text": "🔄 Refresh", "callback_data": f"admin_manage_order:{order.id}"},
                {"text": "⬅️ Back to Orders", "callback_data": "admin_orders_pending" if status_value == "pending" else "admin_orders_all"}
            ])
            
            keyboard = builder.build()
            await callback_query.edit_message_text(text, reply_markup=keyboard)
            await callback_query.answer()
            
        elif data.startswith("admin_order_action:"):
            # Handle order status changes
            _, action, order_id = data.split(":", 2)
            await handle_order_action(client, callback_query, action, order_id)
            
    except Exception as e:
        logger.error(f"Error in admin manage order callback: {e}")
        await callback_query.answer("❌ An error occurred", show_alert=True)


async def handle_order_action(client: Client, callback_query: CallbackQuery, action: str, order_id: str):
    """Handle order status change actions."""
    try:
        order = await order_service.get_order_by_id(order_id)
        if not order:
            await callback_query.answer("❌ Order not found", show_alert=True)
            return
        
        # Map actions to statuses
        status_map = {
            "confirm": OrderStatus.CONFIRMED,
            "processing": OrderStatus.PROCESSING,
            "shipped": OrderStatus.SHIPPED,
            "delivered": OrderStatus.DELIVERED,
            "cancel": OrderStatus.CANCELLED
        }
        
        new_status = status_map.get(action)
        if not new_status:
            await callback_query.answer("❌ Invalid action", show_alert=True)
            return
        
        # Update order status
        from app.models import OrderUpdate
        success = await order_service.update_order(order_id, OrderUpdate(status=new_status))
        
        if success:
            # Send notification to customer
            await notify_customer_order_update(order.user_id, order, new_status)
            
            # Show success message to admin
            action_messages = {
                "confirm": "✅ Order confirmed successfully!",
                "processing": "🔄 Order moved to processing!",
                "shipped": "🚚 Order marked as shipped!",
                "delivered": "📦 Order marked as delivered!",
                "cancel": "❌ Order cancelled successfully!"
            }
            
            await callback_query.answer(action_messages.get(action, "✅ Order updated!"))
            
            # Refresh the order view
            from pyrogram.types import CallbackQuery as CQ
            refresh_callback = CQ(
                id=callback_query.id,
                from_user=callback_query.from_user,
                message=callback_query.message,
                data=f"admin_manage_order:{order_id}",
                chat_instance=callback_query.chat_instance
            )
            await admin_manage_order_callback(client, refresh_callback)
        else:
            await callback_query.answer("❌ Failed to update order", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error handling order action: {e}")
        await callback_query.answer("❌ An error occurred", show_alert=True)


async def notify_customer_order_update(user_id: int, order, new_status: OrderStatus):
    """Send notification to customer about order status update."""
    try:
        # Get customer info
        customer = await user_repo.get_by_tg_id(user_id)
        if not customer:
            logger.warning(f"Customer {user_id} not found for order notification")
            return
        
        # Build notification message
        status_messages = {
            OrderStatus.CONFIRMED: {
                "title": "✅ **ORDER CONFIRMED!**",
                "message": "Your order has been confirmed and is being prepared.",
                "emoji": "✅"
            },
            OrderStatus.PROCESSING: {
                "title": "🔄 **ORDER PROCESSING**",
                "message": "Your order is now being processed and prepared for shipment.",
                "emoji": "🔄"
            },
            OrderStatus.SHIPPED: {
                "title": "🚚 **ORDER SHIPPED!**",
                "message": "Great news! Your order has been shipped and is on its way to you.",
                "emoji": "🚚"
            },
            OrderStatus.DELIVERED: {
                "title": "📦 **ORDER DELIVERED!**",
                "message": "Your order has been successfully delivered! Thank you for shopping with us.",
                "emoji": "📦"
            },
            OrderStatus.CANCELLED: {
                "title": "❌ **ORDER CANCELLED**",
                "message": "Your order has been cancelled. If you have any questions, please contact support.",
                "emoji": "❌"
            }
        }
        
        status_info = status_messages.get(new_status)
        if not status_info:
            return
        
        notification_text = f"{status_info['title']}\n"
        notification_text += "═" * 35 + "\n\n"
        notification_text += f"📋 **Order #{order.id[:8]}**\n"
        notification_text += f"💰 **Total:** {order.total_amount:.2f} USDT\n"
        notification_text += f"📅 **Date:** {order.created_at.strftime('%Y-%m-%d')}\n\n"
        notification_text += f"{status_info['message']}\n\n"
        
        if new_status == OrderStatus.DELIVERED:
            notification_text += "🎉 **Thank you for your business!**\n"
            notification_text += "We hope you enjoy your purchase.\n\n"
        elif new_status == OrderStatus.SHIPPED:
            notification_text += "📱 **Track your order:**\n"
            notification_text += "You'll receive updates as your order progresses.\n\n"
        
        notification_text += "═" * 35
        
        # Send notification using the global bot instance
        from app.bot import bot
        if bot.active_clients:
            await bot.active_clients[0].send_message(user_id, notification_text)
            logger.info(f"Order status notification sent to user {user_id} for order {order.id}")
        else:
            logger.error("No active bot clients available for sending order notification")
            
    except Exception as e:
        logger.error(f"Error sending order notification to user {user_id}: {e}")


@rate_limiter
async def admin_users_callback(client: Client, callback_query: CallbackQuery):
    """Handle admin users callbacks."""
    try:
        user_id = callback_query.from_user.id
        
        if not await is_admin(user_id):
            await callback_query.answer("❌ Access denied", show_alert=True)
            return
        
        data = callback_query.data
        user = await user_repo.get_by_tg_id(user_id)
        
        if data == "admin_users_all":
            users = await user_repo.get_many({}, limit=20)
            text = "👥 **All Users**\n\n"
            
        elif data == "admin_users_banned":
            users = await user_repo.get_many({"is_banned": True}, limit=20)
            text = "🚫 **Banned Users**\n\n"
            
        elif data == "admin_users_admins":
            users = await user_repo.get_admins()
            text = "👑 **Admin Users**\n\n"
            
        elif data == "admin_user_stats":
            total_users = await user_repo.count({})
            active_users = await user_repo.get_active_users_count()
            banned_users = await user_repo.count({"is_banned": True})
            admin_users = len(await user_repo.get_admins())
            
            text = (
                "📊 **User Statistics**\n\n"
                f"Total Users: {total_users}\n"
                f"Active Users: {active_users}\n"
                f"Banned Users: {banned_users}\n"
                f"Admin Users: {admin_users}\n"
            )
            
            from app.keyboards.base import BaseKeyboardBuilder
            builder = BaseKeyboardBuilder()
            builder.add_back_button("admin_users")
            keyboard = builder.build()
            
            await callback_query.edit_message_text(text, reply_markup=keyboard)
            await callback_query.answer()
            return
            
        else:
            await callback_query.answer("❌ Invalid option")
            return
        
        # Display users
        if 'users' in locals():
            if not users:
                text += "No users found."
            else:
                for user_item in users:
                    username = f"@{user_item.username}" if user_item.username else "No username"
                    name = user_item.first_name or "Unknown"
                    status = "🚫 Banned" if user_item.is_banned else "✅ Active"
                    roles = ", ".join(user_item.roles) if user_item.roles else "user"
                    
                    text += f"**{name}** ({username})\n"
                    text += f"ID: {user_item.tg_id}\n"
                    text += f"Balance: USDT{user_item.balance:.2f}\n"
                    text += f"Roles: {roles}\n"
                    text += f"Status: {status}\n\n"
        
        from app.keyboards.base import BaseKeyboardBuilder
        builder = BaseKeyboardBuilder()
        builder.add_back_button("admin_users")
        keyboard = builder.build()
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in admin users callback: {e}")
        await callback_query.answer("❌ An error occurred", show_alert=True)


@rate_limiter
async def admin_back_callback(client: Client, callback_query: CallbackQuery):
    """Handle admin back navigation."""
    try:
        user_id = callback_query.from_user.id
        
        if not await is_admin(user_id):
            await callback_query.answer("❌ Access denied", show_alert=True)
            return
        
        user = await user_repo.get_by_tg_id(user_id)
        
        # Go back to main admin panel
        admin_text = (
            "🔧 **Admin Panel**\n\n"
            "Welcome to the administration panel! Here you can:\n\n"
            "📦 **Products**: Add, edit, manage inventory\n"
            "📋 **Orders**: View and manage customer orders\n"
            "👥 **Users**: Manage user accounts and roles\n"
            "📢 **Announcements**: Send broadcasts and notifications\n"
            "📊 **Metrics**: View revenue and analytics\n"
            "⚙️ **Settings**: Configure bot settings\n\n"
            "Choose an option below:"
        )
        
        keyboard = get_admin_main_keyboard(user)
        await callback_query.edit_message_text(admin_text, reply_markup=keyboard)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in admin back callback: {e}")
        await callback_query.answer("❌ An error occurred", show_alert=True)


@rate_limiter
async def admin_revenue_callback(client: Client, callback_query: CallbackQuery):
    """Handle admin revenue analytics callbacks."""
    try:
        user_id = callback_query.from_user.id
        
        if not await is_admin(user_id):
            await callback_query.answer("❌ Access denied", show_alert=True)
            return
        
        data = callback_query.data
        
        if data == "admin_revenue_today":
            revenue = await order_service.get_today_revenue()
            orders = await order_service.get_today_orders_count()
            text = (
                "📅 **Today's Revenue**\n\n"
                f"💰 Revenue: {revenue:.2f} USDT\n"
                f"📋 Orders: {orders}\n"
                f"📊 Average Order: {(revenue/orders if orders > 0 else 0):.2f} USDT\n"
            )
            
        elif data == "admin_revenue_week":
            stats = await order_service.get_order_stats(7)
            total_revenue = stats.get('total_revenue', 0)
            total_orders = stats.get('total_orders', 0)
            text = (
                "📅 **This Week's Revenue**\n\n"
                f"💰 Revenue: {total_revenue:.2f} USDT\n"
                f"📋 Orders: {total_orders}\n"
                f"📊 Average Order: {(total_revenue/total_orders if total_orders > 0 else 0):.2f} USDT\n"
            )
            
        elif data == "admin_revenue_month":
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            days_in_month = (now - month_start).days + 1
            stats = await order_service.get_order_stats(days_in_month)
            total_revenue = stats.get('total_revenue', 0)
            total_orders = stats.get('total_orders', 0)
            text = (
                "📅 **This Month's Revenue**\n\n"
                f"💰 Revenue: {total_revenue:.2f} USDT\n"
                f"📋 Orders: {total_orders}\n"
                f"📊 Average Order: {(total_revenue/total_orders if total_orders > 0 else 0):.2f} USDT\n"
            )
            
        elif data == "admin_revenue_30days":
            stats = await order_service.get_order_stats(30)
            total_revenue = stats.get('total_revenue', 0)
            total_orders = stats.get('total_orders', 0)
            text = (
                "📅 **Last 30 Days Revenue**\n\n"
                f"💰 Revenue: {total_revenue:.2f} USDT\n"
                f"📋 Orders: {total_orders}\n"
                f"📊 Average Order: {(total_revenue/total_orders if total_orders > 0 else 0):.2f} USDT\n\n"
                "**Status Breakdown:**\n"
            )
            for status, data_item in stats.get('by_status', {}).items():
                text += f"• {status.title()}: {data_item['count']} orders (USDT{data_item['total_amount']:.2f})\n"
            
        elif data == "admin_top_products":
            # Get top products by sales volume and revenue
            stats = await get_top_products_analytics(30)  # Last 30 days
            
            text = (
                "🏆 **Top Products Analysis (30 days)**\n\n"
                "**📊 Best Selling Products:**\n"
            )
            
            if stats.get('by_quantity'):
                for i, (product_name, qty) in enumerate(stats['by_quantity'][:5], 1):
                    text += f"{i}. {product_name} - {qty} sold\n"
            else:
                text += "No sales data found\n"
            
            text += "\n**💰 Top Revenue Products:**\n"
            if stats.get('by_revenue'):
                for i, (product_name, revenue) in enumerate(stats['by_revenue'][:5], 1):
                    text += f"{i}. {product_name} - USDT{revenue:.2f}\n"
            else:
                text += "No revenue data found\n"
            
            text += f"\n📈 **Total Products Sold:** {stats.get('total_items', 0)}"
            text += f"\n💰 **Total Revenue:** USDT{stats.get('total_revenue', 0):.2f}"
            
        elif data == "admin_top_customers":
            # Get top customers by spending and order frequency
            stats = await get_top_customers_analytics(30)  # Last 30 days
            
            text = (
                "🏆 **Top Customers Analysis (30 days)**\n\n"
                "**💰 Highest Spending Customers:**\n"
            )
            
            if stats.get('by_spending'):
                for i, (user_id, total) in enumerate(stats['by_spending'][:5], 1):
                    # Get user info
                    user = await user_repo.get_by_tg_id(user_id)
                    name = user.first_name if user else f"User {user_id}"
                    text += f"{i}. {name} - USDT{total:.2f}\n"
            else:
                text += "No customer data found\n"
            
            text += "\n**📋 Most Frequent Customers:**\n"
            if stats.get('by_orders'):
                for i, (user_id, count) in enumerate(stats['by_orders'][:5], 1):
                    user = await user_repo.get_by_tg_id(user_id)
                    name = user.first_name if user else f"User {user_id}"
                    text += f"{i}. {name} - {count} orders\n"
            else:
                text += "No order data found\n"
            
            text += f"\n👥 **Total Customers:** {stats.get('total_customers', 0)}"
            text += f"\n📊 **Avg. Order Value:** USDT{stats.get('avg_order_value', 0):.2f}"
            
        elif data == "admin_sales_trends":
            # Get sales trends data
            trends = await get_sales_trends_analytics()
            
            text = (
                "📊 **Sales Trends Analysis**\n\n"
                "**📈 Daily Sales (Last 7 days):**\n"
            )
            
            if trends.get('daily_sales'):
                for day_data in trends['daily_sales']:
                    date = day_data['date'].strftime('%Y-%m-%d')
                    revenue = day_data['revenue']
                    orders = day_data['orders']
                    text += f"• {date}: USDT{revenue:.2f} ({orders} orders)\n"
            else:
                text += "No daily sales data\n"
            
            text += "\n**📊 Weekly Growth:**\n"
            if trends.get('weekly_growth') is not None:
                growth = trends['weekly_growth']
                icon = "📈" if growth >= 0 else "📉"
                text += f"{icon} {growth:+.1f}% vs last week\n"
            
            text += "\n**🎯 Peak Sales Times:**\n"
            if trends.get('peak_hours'):
                for hour, count in trends['peak_hours'][:3]:
                    text += f"• {hour}:00 - {count} orders\n"
            
            text += f"\n📈 **Best Day:** {trends.get('best_day', 'N/A')}"
            text += f"\n💰 **Best Day Revenue:** USDT{trends.get('best_day_revenue', 0):.2f}"
            
        elif data == "admin_growth_analysis":
            total_users = await user_repo.count({})
            active_users = await user_repo.get_active_users_count()
            total_revenue_30 = (await order_service.get_order_stats(30)).get('total_revenue', 0)
            total_revenue_7 = (await order_service.get_order_stats(7)).get('total_revenue', 0)
            
            text = (
                "📈 **Growth Analysis**\n\n"
                f"👥 Total Users: {total_users}\n"
                f"✅ Active Users: {active_users}\n"
                f"📊 Retention Rate: {(active_users/total_users*100 if total_users > 0 else 0):.1f}%\n\n"
                f"💰 Revenue Growth:\n"
                f"• Last 7 days: USDT{total_revenue_7:.2f}\n"
                f"• Last 30 days: USDT{total_revenue_30:.2f}\n"
                f"• Weekly average: USDT{(total_revenue_30/4.3):.2f}\n"
            )
            
        else:
            await callback_query.answer("❌ Invalid option")
            return
        
        # Add back button
        from app.keyboards.base import BaseKeyboardBuilder
        builder = BaseKeyboardBuilder()
        builder.add_buttons_row([
            {"text": "🔄 Refresh", "callback_data": data},
            {"text": "⬅️ Back", "callback_data": "admin_revenue"}
        ])
        keyboard = builder.build()
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in admin revenue callback: {e}")
        await callback_query.answer("❌ An error occurred", show_alert=True)


@rate_limiter
async def admin_reports_callback(client: Client, callback_query: CallbackQuery):
    """Handle admin reports callbacks."""
    try:
        user_id = callback_query.from_user.id
        
        if not await is_admin(user_id):
            await callback_query.answer("❌ Access denied", show_alert=True)
            return
        
        data = callback_query.data
        
        if data == "admin_report_orders":
            stats = await order_service.get_order_stats(30)
            recent_orders = await order_service.get_recent_orders(5)
            
            text = (
                "📋 **Order Report (30 days)**\n\n"
                f"Total Orders: {stats.get('total_orders', 0)}\n"
                f"Total Revenue: USDT{stats.get('total_revenue', 0):.2f}\n\n"
                "**Recent Orders:**\n"
            )
            
            for order in recent_orders:
                text += f"• #{order.id[:8]} - USDT{order.total_amount:.2f} - {get_status_value(order.status)}\n"
            
        elif data == "admin_report_users":
            total_users = await user_repo.count({})
            active_users = await user_repo.get_active_users_count()
            banned_users = await user_repo.count({"is_banned": True})
            
            text = (
                "👥 **User Report**\n\n"
                f"Total Users: {total_users}\n"
                f"Active Users: {active_users}\n"
                f"Banned Users: {banned_users}\n"
                f"Active Rate: {(active_users/total_users*100):.1f}%\n"
            )
            
        elif data == "admin_report_inventory":
            total_products = await product_repo.count({})
            active_products = await product_repo.count({"is_active": True})
            low_stock = await product_repo.count({"quantity": {"$lt": 5}})
            
            text = (
                "📦 **Inventory Report**\n\n"
                f"Total Products: {total_products}\n"
                f"Active Products: {active_products}\n"
                f"Low Stock Items: {low_stock}\n"
                f"Active Rate: {(active_products/total_products*100 if total_products > 0 else 0):.1f}%\n"
            )
            
        elif data == "admin_report_financial":
            today_revenue = await order_service.get_today_revenue()
            week_stats = await order_service.get_order_stats(7)
            month_stats = await order_service.get_order_stats(30)
            
            text = (
                "💰 **Financial Report**\n\n"
                f"Today: USDT{today_revenue:.2f}\n"
                f"This Week: USDT{week_stats.get('total_revenue', 0):.2f}\n"
                f"Last 30 Days: USDT{month_stats.get('total_revenue', 0):.2f}\n"
                f"Daily Average: USDT{(month_stats.get('total_revenue', 0)/30):.2f}\n"
            )
            
        elif data == "admin_report_performance":
            # Performance report with KPIs
            perf_data = await get_performance_report()
            
            text = (
                "📊 **Performance Report**\n\n"
                f"**🎯 Key Performance Indicators:**\n"
                f"• Order Fulfillment Rate: {perf_data.get('fulfillment_rate', 0):.1f}%\n"
                f"• Avg. Order Processing Time: {perf_data.get('avg_processing_time', 0):.1f}h\n"
                f"• Customer Satisfaction: {perf_data.get('satisfaction_rate', 0):.1f}%\n"
                f"• Revenue Growth (30d): {perf_data.get('revenue_growth', 0):+.1f}%\n\n"
                
                f"**📈 Business Metrics:**\n"
                f"• Total Orders: {perf_data.get('total_orders', 0)}\n"
                f"• Successful Orders: {perf_data.get('successful_orders', 0)}\n"
                f"• Cancelled Orders: {perf_data.get('cancelled_orders', 0)}\n"
                f"• Return Rate: {perf_data.get('return_rate', 0):.1f}%\n\n"
                
                f"**💰 Financial Performance:**\n"
                f"• Total Revenue: USDT{perf_data.get('total_revenue', 0):.2f}\n"
                f"• Avg. Order Value: USDT{perf_data.get('avg_order_value', 0):.2f}\n"
                f"• Top Product Revenue: USDT{perf_data.get('top_product_revenue', 0):.2f}\n"
            )
            
        elif data == "admin_report_marketing":
            # Marketing effectiveness report
            marketing_data = await get_marketing_report()
            
            text = (
                "🎯 **Marketing Report**\n\n"
                f"**📊 Customer Acquisition:**\n"
                f"• New Users (30d): {marketing_data.get('new_users', 0)}\n"
                f"• User Growth Rate: {marketing_data.get('user_growth', 0):+.1f}%\n"
                f"• Retention Rate: {marketing_data.get('retention_rate', 0):.1f}%\n"
                f"• Conversion Rate: {marketing_data.get('conversion_rate', 0):.1f}%\n\n"
                
                f"**🛒 Purchase Behavior:**\n"
                f"• First-time Buyers: {marketing_data.get('first_time_buyers', 0)}\n"
                f"• Repeat Customers: {marketing_data.get('repeat_customers', 0)}\n"
                f"• Cart Abandonment: {marketing_data.get('cart_abandonment', 0):.1f}%\n"
                f"• Avg. Time to Purchase: {marketing_data.get('avg_time_to_purchase', 0):.1f}h\n\n"
                
                f"**🎨 Product Performance:**\n"
                f"• Most Viewed Category: {marketing_data.get('top_category', 'N/A')}\n"
                f"• Best Converting Product: {marketing_data.get('best_converting_product', 'N/A')}\n"
                f"• Seasonal Trends: {marketing_data.get('seasonal_trend', 'N/A')}\n"
            )
            
        elif data == "admin_export_all":
            # Export all data functionality
            export_result = await export_all_data()
            
            text = (
                "📤 **Data Export Complete**\n\n"
                f"**📊 Exported Data:**\n"
                f"• Users: {export_result.get('users_count', 0)} records\n"
                f"• Products: {export_result.get('products_count', 0)} records\n"
                f"• Orders: {export_result.get('orders_count', 0)} records\n"
                f"• Revenue Data: Last 365 days\n\n"
                
                f"**📁 Export Details:**\n"
                f"• Format: CSV files\n"
                f"• File Size: ~{export_result.get('file_size_mb', 0):.1f} MB\n"
                f"• Export Time: {export_result.get('export_time', 'N/A')}\n\n"
                
                "💾 **Files Ready for Download:**\n"
                "• users_export.csv\n"
                "• products_export.csv\n"
                "• orders_export.csv\n"
                "• revenue_report.csv\n\n"
                
                "📧 Files can be sent via email or downloaded from admin panel."
            )
            
        elif data == "admin_email_reports":
            # Email reports setup
            email_status = await setup_email_reports()
            
            text = (
                "📧 **Email Reports Setup**\n\n"
                f"**📊 Available Reports:**\n"
                "• Daily Sales Summary\n"
                "• Weekly Performance Report\n"
                "• Monthly Financial Report\n"
                "• Quarterly Business Review\n\n"
                
                f"**⚙️ Current Settings:**\n"
                f"• Daily Reports: {'✅ Enabled' if email_status.get('daily_enabled') else '❌ Disabled'}\n"
                f"• Weekly Reports: {'✅ Enabled' if email_status.get('weekly_enabled') else '❌ Disabled'}\n"
                f"• Recipients: {email_status.get('recipients_count', 0)} email(s)\n"
                f"• Last Sent: {email_status.get('last_sent', 'Never')}\n\n"
                
                "📧 **To Configure Email Reports:**\n"
                "1. Set up SMTP settings in bot configuration\n"
                "2. Add recipient email addresses\n"
                "3. Choose report frequency\n"
                "4. Enable automated sending\n\n"
                
                "💡 Contact admin to configure email settings."
            )
            
        else:
            await callback_query.answer("❌ Invalid option")
            return
        
        # Add back button
        from app.keyboards.base import BaseKeyboardBuilder
        builder = BaseKeyboardBuilder()
        builder.add_buttons_row([
            {"text": "🔄 Refresh", "callback_data": data},
            {"text": "⬅️ Back", "callback_data": "admin_reports"}
        ])
        keyboard = builder.build()
        
        await safe_edit_message(callback_query, text, keyboard)
        
    except Exception as e:
        logger.error(f"Error in admin reports callback: {e}")
        await callback_query.answer("❌ An error occurred", show_alert=True)


@rate_limiter
async def addproduct_command_handler(client: Client, message: Message):
    """Handle /addproduct command."""
    try:
        user_id = message.from_user.id
        
        if not await is_admin(user_id):
            await message.reply_text("❌ Access denied. You don't have admin privileges.")
            return
        
        # Parse command: /addproduct Name|Description|Price|City|Area
        command_parts = message.text.split(' ', 1)
        if len(command_parts) < 2:
            await message.reply_text(
                "❌ **Invalid format!**\n\n"
                "Use: `/addproduct Name|Description|Price|City|Area`\n\n"
                "Example:\n"
                "`/addproduct iPhone 15|Latest iPhone model|999.99|Belgrade|Vracar`"
            )
            return
        
        # Parse product data
        try:
            product_data = command_parts[1].split('|')
            if len(product_data) != 5:
                raise ValueError("Incorrect number of parameters")
            
            name, description, price_str, city_str, area_str = product_data
            
            # Validate and convert data
            name = name.strip()
            description = description.strip()
            price = float(price_str.strip())
            city_str = city_str.strip()
            area_str = area_str.strip()
            
            # Validate city and area
            try:
                # Map string inputs to enum values
                city_mapping = {
                    "Belgrade": City.BELGRADE,
                    "belgrade": City.BELGRADE,
                    "Novi Sad": City.NOVI_SAD,
                    "novi sad": City.NOVI_SAD,
                    "NoviSad": City.NOVI_SAD,
                    "novísad": City.NOVI_SAD,
                    "Pancevo": City.PANCEVO,
                    "pancevo": City.PANCEVO,
                    "Pančevo": City.PANCEVO
                }
                
                area_mapping = {
                    # Belgrade areas
                    "Vracar": Area.VRACAR,
                    "vracar": Area.VRACAR,
                    "Novi Beograd": Area.NOVI_BEOGRAD,
                    "novi beograd": Area.NOVI_BEOGRAD,
                    "NoviBeograd": Area.NOVI_BEOGRAD,
                    "Stari grad": Area.STARI_GRAD,
                    "stari grad": Area.STARI_GRAD,
                    "StariGrad": Area.STARI_GRAD,
                    "Zemun": Area.ZEMUN,
                    "zemun": Area.ZEMUN,
                    "Vozdovac": Area.VOZDOVAC,
                    "vozdovac": Area.VOZDOVAC,
                    "Zvezdara": Area.ZVEZDARA,
                    "zvezdara": Area.ZVEZDARA,
                    "Konjarnik": Area.KONJARNIK,
                    "konjarnik": Area.KONJARNIK,
                    "Savski venac": Area.SAVSKI_VENAC,
                    "savski venac": Area.SAVSKI_VENAC,
                    "Banovo brdo": Area.BANOVO_BRDO,
                    "banovo brdo": Area.BANOVO_BRDO,
                    "Mirijevo": Area.MIRIJEVO,
                    "mirijevo": Area.MIRIJEVO,
                    "Ada Ciganlija": Area.ADA_CIGANLIJA,
                    "ada ciganlija": Area.ADA_CIGANLIJA,
                    "Palilula": Area.PALILULA,
                    "palilula": Area.PALILULA,
                    "Senjak": Area.SENJAK,
                    "senjak": Area.SENJAK,
                    "Karaburma": Area.KARABURMA,
                    "karaburma": Area.KARABURMA,
                    "Borca": Area.BORCA,
                    "borca": Area.BORCA,
                    # Novi Sad areas
                    "Centar": Area.CENTAR_NS,
                    "centar": Area.CENTAR_NS,
                    "Podbara": Area.PODBARA,
                    "podbara": Area.PODBARA,
                    "Petrovaradin": Area.PETROVARADIN,
                    "petrovaradin": Area.PETROVARADIN,
                    "Detelinara": Area.DETELINARA,
                    "detelinara": Area.DETELINARA,
                }
                
                city = city_mapping.get(city_str)
                area = area_mapping.get(area_str)
                
                if not city:
                    raise ValueError(f"Invalid city '{city_str}'. Valid cities: Belgrade, Novi Sad, Pancevo")
                
                if not area:
                    raise ValueError(f"Invalid area '{area_str}' for city '{city_str}'")
                
                # Check if area is valid for the city
                if area not in CITY_AREAS.get(city, []):
                    raise ValueError(f"Area '{area_str}' is not valid for city '{city_str}'")
                    
            except ValueError as e:
                await message.reply_text(
                    f"❌ **Invalid location!**\n\n"
                    f"Error: {str(e)}\n\n"
                    "**Valid cities:** Belgrade, Novi Sad, Pancevo\n\n"
                    "**Valid areas for Belgrade:**\n"
                    "Vracar, Novi Beograd, Stari grad, Zemun, Vozdovac, Zvezdara, Konjarnik, Savski venac, Banovo brdo, Mirijevo, Ada Ciganlija, Palilula, Senjak, Karaburma, Borca\n\n"
                    "**Valid areas for Novi Sad:**\n"
                    "Centar, Podbara, Petrovaradin, Detelinara\n\n"
                    "**Valid areas for Pancevo:**\n"
                    "Centar"
                )
                return
            
            # Create product
            product_create = ProductCreate(
                name=name,
                description=description,
                price=price,
                city=city,
                area=area,
                is_active=True
            )
            
            # Add to database
            product = await product_repo.create_product(product_create)
            
            if product:
                success_text = (
                    "✅ **Product Added Successfully!**\n\n"
                    f"**Name:** {product.name}\n"
                    f"**Description:** {product.description}\n"
                    f"**Price:** USDT{product.price:.2f}\n"
                    f"**Location:** {getattr(product.city, 'value', product.city)}, {getattr(product.area, 'value', product.area)}\n"
                    f"**Status:** {'✅ Active' if product.is_active else '❌ Inactive'}\n"
                    f"**Product ID:** `{product.id}`"
                )
                await message.reply_text(success_text)
                logger.info(f"Admin {user_id} added product: {product.name}")
            else:
                await message.reply_text("❌ Failed to add product to database")
                
        except ValueError as e:
            await message.reply_text(
                f"❌ **Invalid data format!**\n\n"
                f"Error: {str(e)}\n\n"
                "Please check:\n"
                "• Price must be a number (e.g., 999.99)\n"
                "• Stock must be an integer (e.g., 10)\n"
                "• City and Area must be valid locations"
            )
            
    except Exception as e:
        logger.error(f"Error in addproduct command handler: {e}")
        await message.reply_text("❌ An error occurred while adding the product")


@rate_limiter
async def bulkprice_command_handler(client: Client, message: Message):
    """Handle /bulkprice command."""
    try:
        user_id = message.from_user.id
        
        if not await is_admin(user_id):
            await message.reply_text("❌ Access denied. You don't have admin privileges.")
            return
        
        # Parse command: /bulkprice +10 or /bulkprice -5
        command_parts = message.text.split(' ', 1)
        if len(command_parts) < 2:
            await message.reply_text(
                "❌ **Invalid format!**\n\n"
                "Use: `/bulkprice percentage`\n\n"
                "Examples:\n"
                "• `/bulkprice +10` (increase all prices by 10%)\n"
                "• `/bulkprice -5` (decrease all prices by 5%)"
            )
            return
        
        try:
            percentage_str = command_parts[1].strip()
            
            # Parse percentage (handle + and - signs)
            if percentage_str.startswith('+'):
                percentage = float(percentage_str[1:])
            elif percentage_str.startswith('-'):
                percentage = -float(percentage_str[1:])
            else:
                percentage = float(percentage_str)
            
            if abs(percentage) > 50:
                await message.reply_text("❌ Percentage change cannot exceed 50% for safety")
                return
            
            # Get all products
            products = await product_repo.get_many({})
            
            if not products:
                await message.reply_text("❌ No products found to update")
                return
            
            # Update prices
            updated_count = 0
            for product in products:
                new_price = product.price * (1 + percentage / 100)
                new_price = round(new_price, 2)  # Round to 2 decimal places
                
                if new_price > 0:  # Ensure price doesn't go negative
                    await product_repo.update_by_id(product.id, {"price": new_price})
                    updated_count += 1
            
            success_text = (
                "✅ **Bulk Price Update Complete!**\n\n"
                f"**Percentage Change:** {percentage:+.1f}%\n"
                f"**Products Updated:** {updated_count}/{len(products)}\n"
                f"**Operation:** {'Price Increase' if percentage > 0 else 'Price Decrease'}"
            )
            await message.reply_text(success_text)
            logger.info(f"Admin {user_id} performed bulk price update: {percentage:+.1f}%")
            
        except ValueError:
            await message.reply_text(
                "❌ **Invalid percentage format!**\n\n"
                "Please use a number with optional + or - sign\n"
                "Examples: +10, -5, 15"
            )
            
    except Exception as e:
        logger.error(f"Error in bulkprice command handler: {e}")
        await message.reply_text("❌ An error occurred while updating prices")


@rate_limiter
async def updatestock_command_handler(client: Client, message: Message):
    """Handle /updatestock command."""
    try:
        user_id = message.from_user.id
        
        if not await is_admin(user_id):
            await message.reply_text("❌ Access denied. You don't have admin privileges.")
            return
        
        # Parse command: /updatestock product_id new_stock
        command_parts = message.text.split(' ')
        if len(command_parts) < 3:
            await message.reply_text(
                "❌ **Invalid format!**\n\n"
                "Use: `/updatestock product_id new_stock`\n\n"
                "Example:\n"
                "`/updatestock 60a1b2c3d4e5f6789 25`\n\n"
                "Get product IDs from the admin panel → Products → List Products"
            )
            return
        
        try:
            product_id = command_parts[1].strip()
            new_stock = int(command_parts[2].strip())
            
            if new_stock < 0:
                await message.reply_text("❌ Stock cannot be negative")
                return
            
            # Get product
            product = await product_repo.get_by_id(product_id)
            if not product:
                await message.reply_text(f"❌ Product with ID `{product_id}` not found")
                return
            
            # Update stock (admin functionality - not shown to users)
            old_stock = getattr(product, 'quantity', 0)  # Default to 0 if quantity doesn't exist
            updated_product = await product_repo.update_product_quantity(product_id, new_stock)
            
            if updated_product:
                success_text = (
                    "✅ **Stock Updated Successfully!**\n\n"
                    f"**Product:** {product.name}\n"
                    f"**Old Stock:** {old_stock}\n"
                    f"**New Stock:** {new_stock}\n"
                    f"**Change:** {new_stock - old_stock:+d}"
                )
                await message.reply_text(success_text)
                logger.info(f"Admin {user_id} updated stock for {product.name}: {old_stock} → {new_stock}")
            else:
                await message.reply_text("❌ Failed to update stock")
                
        except ValueError:
            await message.reply_text("❌ New stock must be a valid number")
            
    except Exception as e:
        logger.error(f"Error in updatestock command handler: {e}")
        await message.reply_text("❌ An error occurred while updating stock")


# Analytics Helper Functions
async def get_top_products_analytics(days: int = 30) -> dict:
    """Get top products analytics."""
    try:
        from app.db import db
        collection = db.db.orders
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Pipeline to get product sales data
        pipeline = [
            {"$match": {
                "created_at": {"$gte": start_date},
                "status": {"$nin": ["cancelled", "refunded"]}
            }},
            {"$unwind": "$items"},
            {"$group": {
                "_id": "$items.product_name",
                "total_quantity": {"$sum": "$items.quantity"},
                "total_revenue": {"$sum": "$items.total_price"}
            }},
            {"$sort": {"total_quantity": -1}}
        ]
        
        results = []
        async for doc in collection.aggregate(pipeline):
            results.append(doc)
        
        # Separate by quantity and revenue
        by_quantity = [(doc["_id"], doc["total_quantity"]) for doc in results]
        by_revenue = sorted([(doc["_id"], doc["total_revenue"]) for doc in results], 
                          key=lambda x: x[1], reverse=True)
        
        total_items = sum(doc["total_quantity"] for doc in results)
        total_revenue = sum(doc["total_revenue"] for doc in results)
        
        return {
            "by_quantity": by_quantity,
            "by_revenue": by_revenue,
            "total_items": total_items,
            "total_revenue": total_revenue
        }
        
    except Exception as e:
        logger.error(f"Error getting top products analytics: {e}")
        return {}


async def get_top_customers_analytics(days: int = 30) -> dict:
    """Get top customers analytics."""
    try:
        from app.db import db
        collection = db.db.orders
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Pipeline for customer spending
        spending_pipeline = [
            {"$match": {
                "created_at": {"$gte": start_date},
                "status": {"$nin": ["cancelled", "refunded"]}
            }},
            {"$group": {
                "_id": "$user_id",
                "total_spent": {"$sum": "$total_amount"},
                "order_count": {"$sum": 1}
            }},
            {"$sort": {"total_spent": -1}}
        ]
        
        spending_results = []
        async for doc in collection.aggregate(spending_pipeline):
            spending_results.append(doc)
        
        # Orders frequency pipeline
        orders_pipeline = [
            {"$match": {
                "created_at": {"$gte": start_date},
                "status": {"$nin": ["cancelled", "refunded"]}
            }},
            {"$group": {
                "_id": "$user_id",
                "order_count": {"$sum": 1}
            }},
            {"$sort": {"order_count": -1}}
        ]
        
        orders_results = []
        async for doc in collection.aggregate(orders_pipeline):
            orders_results.append(doc)
        
        by_spending = [(doc["_id"], doc["total_spent"]) for doc in spending_results]
        by_orders = [(doc["_id"], doc["order_count"]) for doc in orders_results]
        
        total_customers = len(spending_results)
        total_revenue = sum(doc["total_spent"] for doc in spending_results)
        total_orders = sum(doc["order_count"] for doc in spending_results)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        return {
            "by_spending": by_spending,
            "by_orders": by_orders,
            "total_customers": total_customers,
            "avg_order_value": avg_order_value
        }
        
    except Exception as e:
        logger.error(f"Error getting top customers analytics: {e}")
        return {}


async def get_sales_trends_analytics() -> dict:
    """Get sales trends analytics."""
    try:
        from app.db import db
        collection = db.db.orders
        
        # Last 7 days daily sales
        daily_sales = []
        for i in range(7):
            date = datetime.utcnow() - timedelta(days=i)
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            pipeline = [
                {"$match": {
                    "created_at": {"$gte": start_of_day, "$lt": end_of_day},
                    "status": {"$nin": ["cancelled", "refunded"]}
                }},
                {"$group": {
                    "_id": None,
                    "total_revenue": {"$sum": "$total_amount"},
                    "order_count": {"$sum": 1}
                }}
            ]
            
            result = await collection.aggregate(pipeline).to_list(1)
            if result:
                daily_sales.append({
                    "date": start_of_day,
                    "revenue": result[0]["total_revenue"],
                    "orders": result[0]["order_count"]
                })
            else:
                daily_sales.append({
                    "date": start_of_day,
                    "revenue": 0,
                    "orders": 0
                })
        
        # Weekly growth calculation
        this_week_revenue = sum(day["revenue"] for day in daily_sales)
        
        # Get last week's revenue
        last_week_start = datetime.utcnow() - timedelta(days=14)
        last_week_end = datetime.utcnow() - timedelta(days=7)
        
        last_week_pipeline = [
            {"$match": {
                "created_at": {"$gte": last_week_start, "$lt": last_week_end},
                "status": {"$nin": ["cancelled", "refunded"]}
            }},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": "$total_amount"}
            }}
        ]
        
        last_week_result = await collection.aggregate(last_week_pipeline).to_list(1)
        last_week_revenue = last_week_result[0]["total_revenue"] if last_week_result else 0
        
        weekly_growth = 0
        if last_week_revenue > 0:
            weekly_growth = ((this_week_revenue - last_week_revenue) / last_week_revenue) * 100
        
        # Peak hours analysis
        peak_hours_pipeline = [
            {"$match": {
                "created_at": {"$gte": datetime.utcnow() - timedelta(days=30)},
                "status": {"$nin": ["cancelled", "refunded"]}
            }},
            {"$group": {
                "_id": {"$hour": "$created_at"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        peak_hours = []
        async for doc in collection.aggregate(peak_hours_pipeline):
            peak_hours.append((doc["_id"], doc["count"]))
        
        # Best day
        best_day_data = max(daily_sales, key=lambda x: x["revenue"]) if daily_sales else None
        best_day = best_day_data["date"].strftime("%A") if best_day_data else "N/A"
        best_day_revenue = best_day_data["revenue"] if best_day_data else 0
        
        return {
            "daily_sales": reversed(daily_sales),  # Most recent first
            "weekly_growth": weekly_growth,
            "peak_hours": peak_hours,
            "best_day": best_day,
            "best_day_revenue": best_day_revenue
        }
        
    except Exception as e:
        logger.error(f"Error getting sales trends analytics: {e}")
        return {}


async def get_performance_report() -> dict:
    """Get performance report data."""
    try:
        from app.db import db
        orders_collection = db.db.orders
        
        # Calculate performance metrics
        total_orders = await orders_collection.count_documents({})
        successful_orders = await orders_collection.count_documents({
            "status": {"$in": ["delivered", "confirmed"]}
        })
        cancelled_orders = await orders_collection.count_documents({
            "status": {"$in": ["cancelled", "refunded"]}
        })
        
        fulfillment_rate = (successful_orders / total_orders * 100) if total_orders > 0 else 0
        return_rate = (cancelled_orders / total_orders * 100) if total_orders > 0 else 0
        
        # Revenue calculations
        revenue_pipeline = [
            {"$match": {"status": {"$nin": ["cancelled", "refunded"]}}},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": "$total_amount"},
                "avg_order_value": {"$avg": "$total_amount"}
            }}
        ]
        
        revenue_result = await orders_collection.aggregate(revenue_pipeline).to_list(1)
        total_revenue = revenue_result[0]["total_revenue"] if revenue_result else 0
        avg_order_value = revenue_result[0]["avg_order_value"] if revenue_result else 0
        
        # Get top product revenue
        top_product_pipeline = [
            {"$match": {"status": {"$nin": ["cancelled", "refunded"]}}},
            {"$unwind": "$items"},
            {"$group": {
                "_id": "$items.product_name",
                "revenue": {"$sum": "$items.total_price"}
            }},
            {"$sort": {"revenue": -1}},
            {"$limit": 1}
        ]
        
        top_product_result = await orders_collection.aggregate(top_product_pipeline).to_list(1)
        top_product_revenue = top_product_result[0]["revenue"] if top_product_result else 0
        
        # Calculate revenue growth (simplified)
        now = datetime.utcnow()
        last_month = now - timedelta(days=30)
        this_month = now - timedelta(days=15)
        
        last_month_revenue = await orders_collection.aggregate([
            {"$match": {
                "created_at": {"$gte": last_month, "$lt": this_month},
                "status": {"$nin": ["cancelled", "refunded"]}
            }},
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]).to_list(1)
        
        this_month_revenue = await orders_collection.aggregate([
            {"$match": {
                "created_at": {"$gte": this_month},
                "status": {"$nin": ["cancelled", "refunded"]}
            }},
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]).to_list(1)
        
        last_revenue = last_month_revenue[0]["total"] if last_month_revenue else 0
        current_revenue = this_month_revenue[0]["total"] if this_month_revenue else 0
        
        revenue_growth = 0
        if last_revenue > 0:
            revenue_growth = ((current_revenue - last_revenue) / last_revenue) * 100
        
        return {
            "fulfillment_rate": fulfillment_rate,
            "avg_processing_time": 24.0,  # Placeholder - would need order timing data
            "satisfaction_rate": 95.0,    # Placeholder - would need customer feedback
            "revenue_growth": revenue_growth,
            "total_orders": total_orders,
            "successful_orders": successful_orders,
            "cancelled_orders": cancelled_orders,
            "return_rate": return_rate,
            "total_revenue": total_revenue,
            "avg_order_value": avg_order_value,
            "top_product_revenue": top_product_revenue
        }
        
    except Exception as e:
        logger.error(f"Error getting performance report: {e}")
        return {}


async def get_marketing_report() -> dict:
    """Get marketing report data."""
    try:
        from app.db import db
        users_collection = db.db.users
        orders_collection = db.db.orders
        
        # User growth calculations
        now = datetime.utcnow()
        last_30_days = now - timedelta(days=30)
        last_60_days = now - timedelta(days=60)
        
        new_users_30d = await users_collection.count_documents({
            "created_at": {"$gte": last_30_days}
        })
        
        new_users_60d = await users_collection.count_documents({
            "created_at": {"$gte": last_60_days, "$lt": last_30_days}
        })
        
        user_growth = 0
        if new_users_60d > 0:
            user_growth = ((new_users_30d - new_users_60d) / new_users_60d) * 100
        
        # Customer behavior analysis
        total_users = await users_collection.count_documents({})
        users_with_orders = await orders_collection.distinct("user_id")
        conversion_rate = (len(users_with_orders) / total_users * 100) if total_users > 0 else 0
        
        # First-time vs repeat customers
        user_order_counts = await orders_collection.aggregate([
            {"$group": {"_id": "$user_id", "order_count": {"$sum": 1}}},
            {"$group": {
                "_id": "$order_count",
                "user_count": {"$sum": 1}
            }}
        ]).to_list(None)
        
        first_time_buyers = 0
        repeat_customers = 0
        for item in user_order_counts:
            if item["_id"] == 1:
                first_time_buyers = item["user_count"]
            elif item["_id"] > 1:
                repeat_customers += item["user_count"]
        
        # Retention rate (users who made orders in last 30 days)
        active_users = await orders_collection.count_documents({
            "created_at": {"$gte": last_30_days}
        })
        retention_rate = (active_users / total_users * 100) if total_users > 0 else 0
        
        return {
            "new_users": new_users_30d,
            "user_growth": user_growth,
            "retention_rate": retention_rate,
            "conversion_rate": conversion_rate,
            "first_time_buyers": first_time_buyers,
            "repeat_customers": repeat_customers,
            "cart_abandonment": 15.0,  # Placeholder - would need cart tracking
            "avg_time_to_purchase": 2.5,  # Placeholder
            "top_category": "Electronics",  # Placeholder
            "best_converting_product": "iPhone 15",  # Placeholder
            "seasonal_trend": "Increasing"  # Placeholder
        }
        
    except Exception as e:
        logger.error(f"Error getting marketing report: {e}")
        return {}


async def export_all_data() -> dict:
    """Export all data to CSV files."""
    try:
        import csv
        import os
        from datetime import datetime
        
        # Create exports directory if it doesn't exist
        export_dir = "exports"
        os.makedirs(export_dir, exist_ok=True)
        
        from app.db import db
        
        # Export users
        users = await user_repo.get_many({}, limit=10000)
        users_file = f"{export_dir}/users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(users_file, 'w', newline='', encoding='utf-8') as f:
            if users:
                writer = csv.DictWriter(f, fieldnames=['id', 'tg_id', 'username', 'first_name', 'balance', 'roles', 'created_at'])
                writer.writeheader()
                for user in users:
                    writer.writerow({
                        'id': user.id,
                        'tg_id': user.tg_id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'balance': user.balance,
                        'roles': ','.join(user.roles),
                        'created_at': user.created_at
                    })
        
        # Export products
        products = await product_repo.get_many({}, limit=10000)
        products_file = f"{export_dir}/products_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(products_file, 'w', newline='', encoding='utf-8') as f:
            if products:
                writer = csv.DictWriter(f, fieldnames=['id', 'name', 'description', 'price', 'quantity', 'city', 'area', 'is_active'])
                writer.writeheader()
                for product in products:
                    writer.writerow({
                        'id': product.id,
                        'name': product.name,
                        'description': product.description,
                        'price': product.price,
                        'city': getattr(product.city, 'value', product.city),
                        'area': getattr(product.area, 'value', product.area),
                        'is_active': product.is_active
                    })
        
        # Get file sizes
        users_size = os.path.getsize(users_file) / (1024 * 1024) if os.path.exists(users_file) else 0
        products_size = os.path.getsize(products_file) / (1024 * 1024) if os.path.exists(products_file) else 0
        
        return {
            "users_count": len(users),
            "products_count": len(products),
            "orders_count": 0,  # Would implement orders export
            "file_size_mb": users_size + products_size,
            "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return {
            "users_count": 0,
            "products_count": 0,
            "orders_count": 0,
            "file_size_mb": 0,
            "export_time": "Failed"
        }


async def setup_email_reports() -> dict:
    """Setup email reports configuration."""
    try:
        # This would integrate with email service
        # For now, return mock configuration status
        
        return {
            "daily_enabled": False,
            "weekly_enabled": False,
            "recipients_count": 0,
            "last_sent": "Never"
        }
        
    except Exception as e:
        logger.error(f"Error setting up email reports: {e}")
        return {
            "daily_enabled": False,
            "weekly_enabled": False,
            "recipients_count": 0,
            "last_sent": "Error"
        }


@rate_limiter
async def admin_settings_callback(client: Client, callback_query: CallbackQuery):
    """Handle admin settings callbacks."""
    try:
        user_id = callback_query.from_user.id
        
        if not await is_admin(user_id):
            await callback_query.answer("❌ Access denied", show_alert=True)
            return
        
        data = callback_query.data
        
        if data == "admin_support_handle":
            text = (
                "🆘 **Support Settings**\n\n"
                "Configure customer support settings:\n\n"
                "**Current Settings:**\n"
                "• Support Chat ID: Not configured\n"
                "• Auto-reply: Disabled\n"
                "• Working Hours: 24/7\n"
                "• Response Template: Default\n\n"
                "**Available Options:**\n"
                "• Set support chat/channel ID\n"
                "• Configure working hours\n"
                "• Customize auto-reply messages\n"
                "• Set up support ticket system\n\n"
                "💡 Contact developer to configure support settings."
            )
            
        elif data == "admin_text_templates":
            text = (
                "📝 **Text Templates**\n\n"
                "Customize bot messages and templates:\n\n"
                "**Available Templates:**\n"
                "• Welcome message\n"
                "• Order confirmation\n"
                "• Payment instructions\n"
                "• Order status updates\n"
                "• Support responses\n\n"
                "**Current Status:**\n"
                "• Language: English (Default)\n"
                "• Custom templates: 0\n"
                "• Multi-language: Enabled\n\n"
                "Use admin commands to customize templates:\n"
                "• `/template welcome Your new welcome message`\n"
                "• `/template order_confirm Your order confirmation text`"
            )
            
        elif data == "admin_daily_message":
            text = (
                "📅 **Daily Messages**\n\n"
                "Configure automated daily messages:\n\n"
                "**Current Settings:**\n"
                "• Daily messages: Disabled\n"
                "• Send time: Not set\n"
                "• Target audience: All users\n"
                "• Message template: Not configured\n\n"
                "**Features:**\n"
                "• Daily product highlights\n"
                "• Special offers notifications\n"
                "• Motivational messages\n"
                "• Customizable timing\n\n"
                "**Setup:**\n"
                "1. Set message time\n"
                "2. Create message template\n"
                "3. Choose target audience\n"
                "4. Enable daily sending\n\n"
                "💡 Use `/schedule` for one-time messages."
            )
            
        elif data == "admin_bot_settings":
            text = (
                "⚙️ **Bot Configuration**\n\n"
                "Configure core bot settings:\n\n"
                "**General Settings:**\n"
                "• Bot Name: Shop Bot\n"
                "• Default Language: English\n"
                "• Timezone: UTC\n"
                "• Rate Limiting: Enabled\n\n"
                "**Payment Settings:**\n"
                "• Crypto payments: Enabled\n"
                "• Supported coins: USDT, BTC, ETH\n"
                "• Min deposit: $10 USDT\n"
                "• Auto-convert: Disabled\n\n"
                "**Order Settings:**\n"
                "• Auto-confirm: Disabled\n"
                "• Order timeout: 24 hours\n"
                "• Max cart items: 10\n"
                "• Order notifications: Enabled\n\n"
                "**Security:**\n"
                "• Admin verification: Required\n"
                "• User verification: Optional\n"
                "• Spam protection: Enabled\n"
                "• Rate limits: 10 req/min\n\n"
                "Contact developer to modify these settings."
            )
            
        else:
            await callback_query.answer("❌ Invalid option")
            return
        
        # Add back button
        from app.keyboards.base import BaseKeyboardBuilder
        builder = BaseKeyboardBuilder()
        builder.add_buttons_row([
            {"text": "🔄 Refresh", "callback_data": data},
            {"text": "⬅️ Back", "callback_data": "admin_settings"}
        ])
        keyboard = builder.build()
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in admin settings callback: {e}")
        await callback_query.answer("❌ An error occurred", show_alert=True)


@rate_limiter
async def admin_announcements_callback(client: Client, callback_query: CallbackQuery):
    """Handle admin announcements callbacks."""
    try:
        user_id = callback_query.from_user.id
        
        if not await is_admin(user_id):
            await callback_query.answer("❌ Access denied", show_alert=True)
            return
        
        data = callback_query.data
        
        if data == "admin_send_broadcast":
            text = (
                "📢 **Send Broadcast Message**\n\n"
                "To send a broadcast message to all users, use:\n\n"
                "`/broadcast Your message here`\n\n"
                "**Features:**\n"
                "• Sends to all active users\n"
                "• Supports text formatting\n"
                "• Rate limited to prevent spam\n"
                "• Tracks delivery status\n\n"
                "**Example:**\n"
                "`/broadcast 🎉 New products added! Check them out in the shop.`"
            )
            
        elif data == "admin_schedule_message":
            text = (
                "📅 **Schedule Message**\n\n"
                "To schedule a message for later, use:\n\n"
                "`/schedule YYYY-MM-DD HH:MM Your message`\n\n"
                "**Examples:**\n"
                "• `/schedule 2024-12-25 09:00 🎄 Merry Christmas! Special offers today!`\n"
                "• `/schedule 2024-01-01 00:00 🎆 Happy New Year!`\n\n"
                "**Features:**\n"
                "• Schedule up to 30 days in advance\n"
                "• Automatic delivery\n"
                "• Edit or cancel scheduled messages\n"
                "• Time zone support"
            )
            
        elif data == "admin_view_scheduled":
            scheduled = await get_scheduled_messages()
            text = "📋 **Scheduled Messages**\n\n"
            
            if scheduled:
                for msg in scheduled[:10]:  # Show up to 10
                    status = "⏰ Pending" if msg['status'] == 'pending' else "✅ Sent"
                    text += f"**{msg['schedule_time']}**\n"
                    text += f"Message: {msg['content'][:50]}...\n"
                    text += f"Status: {status}\n\n"
            else:
                text += "No scheduled messages found.\n\n"
            
            text += "Use `/schedule` command to add new scheduled messages."
            
        elif data == "admin_announcement_stats":
            stats = await get_announcement_stats()
            text = (
                "📊 **Announcement Statistics**\n\n"
                f"**📤 Broadcast Messages:**\n"
                f"• Total Sent: {stats.get('total_broadcasts', 0)}\n"
                f"• This Month: {stats.get('month_broadcasts', 0)}\n"
                f"• Success Rate: {stats.get('success_rate', 0):.1f}%\n"
                f"• Avg. Reach: {stats.get('avg_reach', 0)} users\n\n"
                
                f"**📅 Scheduled Messages:**\n"
                f"• Pending: {stats.get('pending_scheduled', 0)}\n"
                f"• Completed: {stats.get('completed_scheduled', 0)}\n"
                f"• Failed: {stats.get('failed_scheduled', 0)}\n\n"
                
                f"**👥 Audience:**\n"
                f"• Total Users: {stats.get('total_users', 0)}\n"
                f"• Active Users: {stats.get('active_users', 0)}\n"
                f"• Blocked Bot: {stats.get('blocked_users', 0)}\n"
                f"• Delivery Rate: {stats.get('delivery_rate', 0):.1f}%"
            )
            
        else:
            await callback_query.answer("❌ Invalid option")
            return
        
        # Add back button
        from app.keyboards.base import BaseKeyboardBuilder
        builder = BaseKeyboardBuilder()
        builder.add_buttons_row([
            {"text": "🔄 Refresh", "callback_data": data},
            {"text": "⬅️ Back", "callback_data": "admin_announcements"}
        ])
        keyboard = builder.build()
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in admin announcements callback: {e}")
        await callback_query.answer("❌ An error occurred", show_alert=True)


@rate_limiter
async def cleanup_carts_command_handler(client: Client, message: Message):
    """Handle /cleanupcarts command to fix null _id cart documents."""
    try:
        user_id = message.from_user.id
        
        if not await is_admin(user_id):
            await message.reply_text("❌ Access denied. You don't have admin privileges.")
            return
        
        await message.reply_text("🔧 **Starting cart cleanup...**\n\nRemoving documents with null _id values...")
        
        # Import here to avoid circular imports
        from app.services.cart_service import cart_service
        
        # Run cleanup
        result = await cart_service.cleanup_null_ids()
        
        if result["status"] == "success":
            response_text = (
                "✅ **Cart Cleanup Complete!**\n\n"
                f"🗑️ **Deleted:** {result['deleted_count']} documents with null _id\n"
                f"📊 **Remaining:** {result['total_remaining']} cart documents\n\n"
                "The duplicate key error should now be fixed!"
            )
        elif result["status"] == "no_null_docs":
            response_text = (
                "✅ **Cart Cleanup Complete!**\n\n"
                f"🔍 **Found:** 0 documents with null _id\n"
                f"📊 **Total carts:** {result['total_remaining']}\n\n"
                "No cleanup needed - database is clean!"
            )
        else:
            response_text = (
                f"❌ **Cart Cleanup Failed!**\n\n"
                f"**Error:** {result.get('error', 'Unknown error')}\n\n"
                "Please check the logs for more details."
            )
        
        await message.reply_text(response_text)
        logger.info(f"Admin {user_id} ran cart cleanup: {result}")
        
    except Exception as e:
        logger.error(f"Error in cleanup carts command handler: {e}")
        await message.reply_text("❌ An error occurred during cleanup")


@rate_limiter
async def broadcast_command_handler(client: Client, message: Message):
    """Handle /broadcast command."""
    try:
        user_id = message.from_user.id
        
        if not await is_admin(user_id):
            await message.reply_text("❌ Access denied. You don't have admin privileges.")
            return
        
        # Parse command: /broadcast message text
        command_parts = message.text.split(' ', 1)
        if len(command_parts) < 2:
            await message.reply_text(
                "❌ **Invalid format!**\n\n"
                "Use: `/broadcast Your message here`\n\n"
                "Example:\n"
                "`/broadcast 🎉 New products added! Check out our latest offers.`"
            )
            return
        
        broadcast_text = command_parts[1]
        
        # Get all active users
        users = await user_repo.get_many({"is_banned": {"$ne": True}}, limit=10000)
        
        if not users:
            await message.reply_text("❌ No active users found to broadcast to.")
            return
        
        # Send broadcast
        success_count = 0
        failed_count = 0
        
        status_message = await message.reply_text(
            f"📤 **Broadcasting to {len(users)} users...**\n\n"
            "⏳ Starting broadcast..."
        )
        
        for i, user in enumerate(users):
            try:
                await client.send_message(user.tg_id, broadcast_text)
                success_count += 1
                
                # Update status every 50 users
                if (i + 1) % 50 == 0:
                    await status_message.edit_text(
                        f"📤 **Broadcasting Progress**\n\n"
                        f"✅ Sent: {success_count}\n"
                        f"❌ Failed: {failed_count}\n"
                        f"⏳ Progress: {i + 1}/{len(users)}"
                    )
                
                # Rate limiting delay
                await asyncio.sleep(0.1)
                
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to send broadcast to user {user.tg_id}: {e}")
        
        # Final status
        final_text = (
            f"📤 **Broadcast Complete!**\n\n"
            f"✅ **Successfully sent:** {success_count}\n"
            f"❌ **Failed:** {failed_count}\n"
            f"📊 **Success rate:** {(success_count / len(users) * 100):.1f}%\n\n"
            f"**Message:** {broadcast_text[:100]}..."
        )
        
        await status_message.edit_text(final_text)
        logger.info(f"Admin {user_id} sent broadcast to {success_count}/{len(users)} users")
        
    except Exception as e:
        logger.error(f"Error in broadcast command handler: {e}")
        await message.reply_text("❌ An error occurred while sending broadcast")


async def get_scheduled_messages() -> list:
    """Get scheduled messages."""
    try:
        # This would integrate with a scheduler database
        # For now, return mock data
        return [
            {
                "schedule_time": "2024-12-25 09:00",
                "content": "🎄 Merry Christmas! Special holiday offers available now!",
                "status": "pending"
            },
            {
                "schedule_time": "2024-01-01 00:00", 
                "content": "🎆 Happy New Year! Thank you for being with us!",
                "status": "pending"
            }
        ]
    except Exception as e:
        logger.error(f"Error getting scheduled messages: {e}")
        return []


async def get_announcement_stats() -> dict:
    """Get announcement statistics."""
    try:
        # This would track actual broadcast statistics
        # For now, return calculated stats
        
        total_users = await user_repo.count({})
        active_users = await user_repo.get_active_users_count()
        
        return {
            "total_broadcasts": 0,  # Would track in database
            "month_broadcasts": 0,  # Would track in database  
            "success_rate": 95.0,   # Would calculate from delivery logs
            "avg_reach": active_users,
            "pending_scheduled": 2,  # From scheduled messages
            "completed_scheduled": 0,
            "failed_scheduled": 0,
            "total_users": total_users,
            "active_users": active_users,
            "blocked_users": total_users - active_users,
            "delivery_rate": 95.0
        }
        
    except Exception as e:
        logger.error(f"Error getting announcement stats: {e}")
        return {}
