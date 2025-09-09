"""User handlers for the bot."""

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from app.db.user_repository import user_repo
from app.db.product_repository import product_repo
from app.services import cart_service, order_service, payment_service
from app.models import UserCreate, LanguageCode, City, Area, CITY_AREAS
from app.keyboards import (
    get_main_menu_keyboard,
    get_city_selection_keyboard,
    get_area_selection_keyboard,
    get_language_keyboard,
    get_products_keyboard,
    get_cart_keyboard,
    get_enhanced_cart_keyboard,
    get_crypto_selection_keyboard,
    get_deposit_confirmation_keyboard
)
from app.i18n import translator, get_user_language
from app.utils.rate_limiter import rate_limiter
from app.utils.validators import validate_amount
from app.models import UserRole
import logging

logger = logging.getLogger(__name__)


async def safe_edit_message(callback_query: CallbackQuery, text: str, reply_markup=None):
    """Safely edit message, handling MESSAGE_NOT_MODIFIED errors."""
    try:
        await callback_query.edit_message_text(text, reply_markup=reply_markup)
        return True
    except Exception as edit_error:
        # Handle MESSAGE_NOT_MODIFIED error gracefully
        if "MESSAGE_NOT_MODIFIED" in str(edit_error):
            # Message content is the same, just answer the callback
            await callback_query.answer()
            return True
        else:
            # Re-raise other errors
            raise edit_error


@rate_limiter
async def start_handler(client: Client, message: Message):
    """Handle /start command."""
    try:
        user_id = message.from_user.id
        
        # Get or create user
        user = await user_repo.get_by_tg_id(user_id)
        if not user:
            user_data = UserCreate(
                tg_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            user = await user_repo.create_user(user_data)
            logger.info(f"Created new user: {user_id}")
        
        # Check if user is banned
        if user.is_banned:
            await message.reply_text("❌ Your account has been banned.")
            return
        
        lang = get_user_language(user)
        welcome_text = translator.get_text("start.welcome", lang)
        keyboard = get_main_menu_keyboard(user)
        
        await message.reply_text(welcome_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await message.reply_text("❌ An error occurred")


@rate_limiter
async def main_menu_callback(client: Client, callback_query: CallbackQuery):
    """Handle main menu callbacks."""
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        logger.info(f"Main menu callback triggered: {data}")
        print(f"\n🎯 MAIN MENU CALLBACK: '{data}' from user {user_id}")
        
        user = await user_repo.get_by_tg_id(user_id)
        if not user or user.is_banned:
            await callback_query.answer("❌ Access denied")
            return
        
        lang = get_user_language(user)
        
        if data == "order_products":
            text = translator.get_text("location.choose_city", lang)
            keyboard = get_city_selection_keyboard(user)
            await callback_query.edit_message_text(text, reply_markup=keyboard)
            
        elif data == "preorder":
            # Show pre-order information and city selection
            text = "📋 **PRE-ORDER SYSTEM**\n\n"
            text += "🎯 **How it works:**\n"
            text += "• Browse available products by location\n"
            text += "• Place orders for items you want\n"
            text += "• We'll notify you when ready for pickup/delivery\n"
            text += "• Pay securely with crypto\n\n"
            text += "📍 **Select your city to start pre-ordering:**"
            
            keyboard = get_city_selection_keyboard(user)
            await callback_query.edit_message_text(text, reply_markup=keyboard)
            
        elif data == "support":
            handle = "@grofshop"  # TODO: Get from settings
            text = translator.get_text("support.message", lang, handle=handle)
            keyboard = get_main_menu_keyboard(user)
            await callback_query.edit_message_text(text, reply_markup=keyboard)
            

            
        elif data == "language":
            text = translator.get_text("language.choose", lang)
            keyboard = get_language_keyboard(user)
            await callback_query.edit_message_text(text, reply_markup=keyboard)
            
        elif data == "my_cart":
            await show_cart(callback_query, user)
            
        elif data == "check_balance":
            await show_balance(callback_query, user)
            
        elif data == "my_orders":
            await show_user_orders(callback_query, user)
            
        elif data == "back_to_main":
            # Clear any user state when going back to main menu
            from app.utils.user_state import user_state_manager
            await user_state_manager.clear_state(user_id)
            
            text = translator.get_text("start.welcome", lang)
            keyboard = get_main_menu_keyboard(user)
            await safe_edit_message(callback_query, text, keyboard)
            
        elif data.startswith("back_to_area:"):
            # Go back to area selection for specific city
            city = data.split(":", 1)[1]
            text = translator.get_text("location.choose_area", lang)
            keyboard = get_area_selection_keyboard(city, user)
            await safe_edit_message(callback_query, text, keyboard)
            
        elif data == "back_to_products":
            # Go back to products list (this will be handled by area_selection_callback)
            await callback_query.answer("Use the area selection to view products")
            
        elif data == "back_to_cities":
            # Go back to city selection
            text = translator.get_text("location.choose_city", lang)
            keyboard = get_city_selection_keyboard(user)
            await safe_edit_message(callback_query, text, keyboard)
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in main menu callback: {e}")
        await callback_query.answer("❌ An error occurred")


async def city_selection_callback(client: Client, callback_query: CallbackQuery):
    """Handle city selection."""
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        if not data.startswith("city:"):
            return
        
        city = data.split(":", 1)[1]
        user = await user_repo.get_by_tg_id(user_id)
        lang = get_user_language(user)
        
        text = translator.get_text("location.choose_area", lang)
        keyboard = get_area_selection_keyboard(city, user)
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in city selection: {e}")
        await callback_query.answer("❌ An error occurred")


async def area_selection_callback(client: Client, callback_query: CallbackQuery):
    """Handle area selection."""
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        if not data.startswith("area:"):
            return
        
        _, city, area = data.split(":", 2)
        user = await user_repo.get_by_tg_id(user_id)
        lang = get_user_language(user)
        
        # Get products for this location
        city_enum = City(city)
        area_enum = Area(area)
        all_products = await product_repo.get_products_by_location(city_enum, area_enum)
        
        # Filter out products with 0 stock (only show available products)
        products = [product for product in all_products if product.quantity > 0]
        
        if not products:
            text = f"📍 **{city}, {area}**\n\n"
            text += "🚫 **No products available in this area**\n\n"
            text += "All items are currently out of stock.\n"
            text += "Try another area or check back later!"
            keyboard = get_area_selection_keyboard(city, user)
            await callback_query.edit_message_text(text, reply_markup=keyboard)
        else:
            text = f"🛍️ **Available Products** - {city}, {area}\n"
            text += f"📦 **{len(products)} items available**"
            keyboard = get_products_keyboard(products, city, area, 1, 1, False, user)
            
            # Create products listing text (no quantity display)
            products_text = text + "\n\n"
            for product in products[:5]:  # Show first 5 products
                # Available badge
                products_text += f"✅ **{product.name}**\n"
                products_text += f"💰 **{product.price:.2f} USDT**\n"
                products_text += f"📝 {product.description[:100]}...\n\n"
            
            if len(products) > 5:
                products_text += f"... and {len(products) - 5} more items"
            
            await callback_query.edit_message_text(products_text, reply_markup=keyboard)
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in area selection: {e}")
        await callback_query.answer("❌ An error occurred")


async def add_to_cart_callback(client: Client, callback_query: CallbackQuery):
    """Handle add to cart."""
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        if not data.startswith("add_to_cart:"):
            return
        
        product_id = data.split(":", 1)[1]
        user = await user_repo.get_by_tg_id(user_id)
        lang = get_user_language(user)
        
        # Get product
        product = await product_repo.get_by_id(product_id)
        if not product or not product.is_active or product.quantity <= 0:
            await callback_query.answer(translator.get_text("products.out_of_stock", lang))
            return
        
        # Add to cart
        success = await cart_service.add_item(user_id, product, 1)
        if success:
            await callback_query.answer(translator.get_text("cart.item_added", lang))
        else:
            await callback_query.answer(translator.get_text("products.out_of_stock", lang))
        
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        await callback_query.answer("❌ An error occurred")


async def show_cart(callback_query: CallbackQuery, user):
    """Show user's cart."""
    try:
        logger.info(f"Showing cart for user {user.tg_id}")
        lang = get_user_language(user)
        logger.info(f"Getting cart summary for user {user.tg_id}")
        cart_summary = await cart_service.get_cart_summary(user.tg_id)
        logger.info(f"Cart summary: {cart_summary}")
        
        if not cart_summary["items"]:
            logger.info("Cart is empty, showing empty cart message")
            text = translator.get_text("cart.empty", lang)
            keyboard = get_main_menu_keyboard(user)
            await safe_edit_message(callback_query, text, keyboard)
            return
        
        # Build cart text with crypto-focused formatting
        logger.info("Building cart display text")
        text = f"🛒 **{translator.get_text('cart.title', lang)}**\n"
        text += "═" * 25 + "\n\n"
        
        # Crypto wallet balance section
        text += "┌─────────────────────┐\n"
        text += f"│ 🪙 **Wallet Balance** │\n"
        text += f"│ **{user.balance:.2f} USDT**      │\n"
        text += "└─────────────────────┘\n\n"
        
        # Cart items
        text += "**🛍️ Cart Items:**\n"
        for i, item in enumerate(cart_summary["items"], 1):
            text += f"{i}. **{item.product_name}**\n"
            text += f"   💰 {item.price:.2f} USDT × {item.quantity} = **{item.total_price:.2f} USDT**\n\n"
        
        # Cart summary
        text += "─" * 25 + "\n"
        text += f"📦 **Total Items:** {cart_summary['items_count']}\n"
        text += f"🪙 **Cart Total:** **{cart_summary['total_amount']:.2f} USDT**\n"
        
        # Payment note
        if user.balance >= cart_summary['total_amount']:
            text += "✅ **Sufficient balance for checkout**\n"
        else:
            needed = cart_summary['total_amount'] - user.balance
            text += f"⚠️ **Need {needed:.2f} USDT more**\n"
        
        text += "─" * 25
        
        # Create enhanced cart keyboard with item management
        logger.info("Creating enhanced cart keyboard")
        keyboard = get_enhanced_cart_keyboard(user, cart_summary["items"])
        logger.info("Displaying cart with safe_edit_message")
        await safe_edit_message(callback_query, text, keyboard)
        logger.info("Cart displayed successfully")
        
    except Exception as e:
        logger.error(f"Error showing cart: {e}")
        try:
            await callback_query.answer("❌ An error occurred")
        except Exception as answer_error:
            logger.error(f"Failed to send error answer: {answer_error}")
            pass


async def checkout_callback(client: Client, callback_query: CallbackQuery):
    """Handle checkout."""
    try:
        user_id = callback_query.from_user.id
        logger.info(f"Checkout callback triggered for user {user_id}")
        print(f"\n🛒 CHECKOUT CALLBACK: User {user_id}")
        
        user = await user_repo.get_by_tg_id(user_id)
        if not user:
            logger.error(f"User {user_id} not found")
            await callback_query.answer("❌ User not found")
            return
            
        lang = get_user_language(user)
        logger.info(f"User found, language: {lang}")
        
        # Create order from cart
        logger.info(f"Creating order from cart for user {user_id}")
        order = await order_service.create_order_from_cart(user)
        logger.info(f"Order creation result: {order}")
        
        if not order:
            logger.info("No order created, checking cart status")
            cart_summary = await cart_service.get_cart_summary(user_id)
            logger.info(f"Cart summary: {cart_summary}")
            
            if not cart_summary["items"]:
                # Cart is empty - could mean order was already processed
                text = "🛒 Your cart is empty. If you just placed an order, it was processed successfully!"
                keyboard = get_main_menu_keyboard(user)
                await safe_edit_message(callback_query, text, keyboard)
                logger.info("Cart is empty - showing empty cart message with main menu")
            elif user.balance < cart_summary["total_amount"]:
                text = translator.get_text("cart.insufficient_balance", lang)
                await callback_query.answer(text)
                logger.info(f"Insufficient balance: {user.balance} < {cart_summary['total_amount']}")
            else:
                text = "❌ An error occurred"
                await callback_query.answer(text)
                logger.error("Unknown error during order creation")
            
            return
        
        # SUCCESS: Order created successfully
        logger.info("Order created successfully, building success message")
        try:
            # Build comprehensive success message
            text = "🎉 **ORDER CREATED SUCCESSFULLY!**\n"
            text += "═" * 35 + "\n\n"
            
            text += f"📋 **Order Details:**\n"
            text += f"• Order ID: `{order.id}`\n"
            text += f"• Items: {len(order.items)} products\n"
            text += f"• Total: **{order.total_amount:.2f} USDT**\n"
            text += f"• Status: ✅ {order.status.upper()}\n\n"
            
            # Payment was automatically deducted from balance
            new_balance = user.balance - order.total_amount
            text += f"💳 **Payment Processed:**\n"
            text += f"• Previous Balance: {user.balance:.2f} USDT\n"
            text += f"• Order Total: -{order.total_amount:.2f} USDT\n"
            text += f"• New Balance: **{new_balance:.2f} USDT**\n\n"
            
            text += "🚀 **What happens next?**\n"
            text += "• Your order is being processed\n"
            text += "• You'll receive updates on order status\n"
            text += "• Delivery will be arranged soon\n\n"
            
            text += "✨ **Thank you for your order!**\n"
            text += "═" * 35
            
            # Create main menu keyboard (order is complete)
            keyboard = get_main_menu_keyboard(user)
            
            logger.info("Editing message with checkout success")
            await safe_edit_message(callback_query, text, keyboard)
            await callback_query.answer("✅ Order placed successfully!")
            logger.info("Checkout success message sent")
            
        except Exception as msg_error:
            logger.error(f"Error building/sending success message: {msg_error}")
            await callback_query.answer("❌ Error displaying checkout")
            return
        
        # Optionally send detailed order breakdown as separate message
        try:
            order_details = f"📦 **Detailed Order Breakdown**\n\n"
            for i, item in enumerate(order.items, 1):
                order_details += f"{i}. **{item.product_name}**\n"
                order_details += f"   💰 {item.price:.2f} USDT × {item.quantity} = {item.total_price:.2f} USDT\n\n"
            
            order_details += f"🧾 **Order Summary:**\n"
            order_details += f"• Total Items: {len(order.items)}\n"
            order_details += f"• Order Total: **{order.total_amount:.2f} USDT**\n"
            order_details += f"• Order Date: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            await client.send_message(user_id, order_details)
            logger.info("Detailed order breakdown sent")
        except Exception as details_error:
            logger.error(f"Error sending order details: {details_error}")
        
        # Send notification to all admins
        try:
            await notify_admins_new_order(client, order, user)
            logger.info("Admin notification sent for new order")
        except Exception as admin_error:
            logger.error(f"Error sending admin notification: {admin_error}")
        
    except Exception as e:
        logger.error(f"Error in checkout: {e}")
        import traceback
        traceback.print_exc()
        try:
            await callback_query.answer("❌ An error occurred during checkout")
        except:
            pass


async def notify_admins_new_order(client: Client, order, user):
    """Send notification to all admins about new order."""
    try:
        # Get all admin users
        admin_users = await user_repo.get_users_by_role(UserRole.ADMIN)
        
        if not admin_users:
            logger.warning("No admin users found to notify")
            return
        
        # Build admin notification message
        admin_message = "🚨 **NEW ORDER RECEIVED!**\n"
        admin_message += "═" * 30 + "\n\n"
        
        # Customer info
        admin_message += f"👤 **Customer:**\n"
        admin_message += f"• Name: {user.first_name}"
        if user.last_name:
            admin_message += f" {user.last_name}"
        admin_message += f"\n• Username: @{user.username}" if user.username else ""
        admin_message += f"\n• User ID: `{user.tg_id}`\n"
        admin_message += f"• Balance: {user.balance:.2f} USDT\n\n"
        
        # Order details
        admin_message += f"📋 **Order Details:**\n"
        admin_message += f"• Order ID: `{order.id}`\n"
        admin_message += f"• Items: {len(order.items)} products\n"
        admin_message += f"• Total: **{order.total_amount:.2f} USDT**\n"
        admin_message += f"• Status: {order.status.upper()}\n"
        admin_message += f"• Payment: {order.payment_method}\n"
        admin_message += f"• Date: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Items breakdown
        admin_message += f"🛍️ **Items Ordered:**\n"
        for i, item in enumerate(order.items, 1):
            admin_message += f"{i}. **{item.product_name}**\n"
            admin_message += f"   💰 {item.price:.2f} USDT × {item.quantity} = {item.total_price:.2f} USDT\n"
        
        admin_message += "\n" + "═" * 30
        admin_message += f"\n💰 **Revenue:** +{order.total_amount:.2f} USDT"
        
        # Send to all admins
        admin_count = 0
        for admin in admin_users:
            try:
                await client.send_message(admin.tg_id, admin_message)
                admin_count += 1
                logger.info(f"Order notification sent to admin {admin.tg_id}")
            except Exception as send_error:
                logger.error(f"Failed to send notification to admin {admin.tg_id}: {send_error}")
        
        logger.info(f"Order notification sent to {admin_count} admins")
        
    except Exception as e:
        logger.error(f"Error notifying admins about new order: {e}")


async def show_user_orders(callback_query: CallbackQuery, user):
    """Show user's order history."""
    try:
        lang = get_user_language(user)
        
        # Get user's orders
        orders = await order_service.get_user_orders(user.tg_id, limit=10)
        
        if not orders:
            text = "📦 **Your Order History**\n\n"
            text += "You haven't placed any orders yet.\n"
            text += "Start shopping to see your orders here! 🛍️"
            
            keyboard = get_main_menu_keyboard(user)
            await safe_edit_message(callback_query, text, keyboard)
            return
        
        # Build orders display
        text = f"📦 **Your Order History** ({len(orders)} orders)\n"
        text += "═" * 30 + "\n\n"
        
        total_spent = 0
        for i, order in enumerate(orders, 1):
            total_spent += order.total_amount
            
            # Order status emoji
            status_emoji = {
                "pending": "⏳",
                "confirmed": "✅", 
                "processing": "🔄",
                "shipped": "🚚",
                "delivered": "📦",
                "cancelled": "❌",
                "refunded": "💸"
            }.get(order.status, "📋")
            
            text += f"**{i}. Order #{order.id[:8]}**\n"
            text += f"   {status_emoji} Status: {order.status.upper()}\n"
            text += f"   💰 Total: {order.total_amount:.2f} USDT\n"
            text += f"   📅 Date: {order.created_at.strftime('%Y-%m-%d')}\n"
            text += f"   🛍️ Items: {len(order.items)} products\n\n"
        
        text += "─" * 30 + "\n"
        text += f"📊 **Total Spent:** {total_spent:.2f} USDT\n"
        text += f"🛒 **Average Order:** {total_spent/len(orders):.2f} USDT"
        
        # Create back button
        from app.keyboards.base import BaseKeyboardBuilder
        builder = BaseKeyboardBuilder()
        builder.add_back_button("back_to_main")
        
        await safe_edit_message(callback_query, text, builder.build())
        
    except Exception as e:
        logger.error(f"Error showing user orders: {e}")
        try:
            await callback_query.answer("❌ Error loading order history")
        except:
            pass


async def show_balance(callback_query: CallbackQuery, user):
    """Show user's crypto-focused balance with beautiful formatting."""
    try:
        lang = get_user_language(user)
        
        # Create crypto-focused balance display
        text = "🪙 **Your Crypto Wallet**\n"
        text += "═" * 28 + "\n\n"
        
        # Main balance card - crypto style
        text += "┌──────────────────────────┐\n"
        text += f"│ 💰 **Wallet Balance**      │\n"
        text += f"│ **{user.balance:.2f} USDT**        │\n"
        text += "└──────────────────────────┘\n\n"
        
        # Crypto status with different approach
        if user.balance >= 100:
            status = "🟢 **High Balance**"
            emoji = "💎"
            tip = "🚀 **Ready to shop!** You have plenty of funds."
        elif user.balance >= 50:
            status = "🟡 **Good Balance**"
            emoji = "✨"
            tip = "💪 **Great!** You can purchase most products."
        elif user.balance >= 10:
            status = "🟠 **Low Balance**"
            emoji = "⚠️"
            tip = "📈 **Consider adding more** USDT for better shopping experience."
        else:
            status = "🔴 **Very Low**"
            emoji = "⚡"
            tip = "💰 **Top up your wallet** to start shopping!"
        
        text += f"{emoji} **Status:** {status}\n\n"
        
        # Crypto wallet info
        text += "**🪙 Crypto Features:**\n"
        text += "• ⚡ Instant deposits via USDT\n"
        text += "• 🔒 Secure crypto payments\n"
        text += "• 📱 Mobile-friendly transactions\n\n"
        
        # Tips section - crypto focused
        text += f"💡 **{tip}**\n\n"
        
        text += "─" * 28
        
        # Create crypto-focused action buttons
        from app.keyboards.base import BaseKeyboardBuilder
        builder = BaseKeyboardBuilder()
        
        # Crypto-focused action buttons
        builder.add_buttons_row([
            {"text": "🛍️ Shop Now", "callback_data": "order_products"},
            {"text": "🛒 View Cart", "callback_data": "my_cart"}
        ])
        
        builder.add_buttons_row([
            {"text": "💰 Deposit USDT", "callback_data": "crypto_deposit"},
            {"text": "🪙 Crypto Rates", "callback_data": "crypto_rates"}
        ])
        
        builder.add_back_button("back_to_main")
        
        await safe_edit_message(callback_query, text, builder.build())
        
    except Exception as e:
        logger.error(f"Error showing balance: {e}")
        await callback_query.answer("❌ An error occurred")


async def language_callback(client: Client, callback_query: CallbackQuery):
    """Handle language selection."""
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        if not data.startswith("lang:"):
            return
        
        language_code = data.split(":", 1)[1]
        
        # Update user language
        await user_repo.set_language(user_id, language_code)
        
        # Show success message in new language
        text = translator.get_text("language.changed", language_code)
        keyboard = get_main_menu_keyboard()
        await safe_edit_message(callback_query, text, keyboard)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in language selection: {e}")
        await callback_query.answer("❌ An error occurred")


async def clear_cart_callback(client: Client, callback_query: CallbackQuery):
    """Handle clear cart action."""
    try:
        user_id = callback_query.from_user.id
        user = await user_repo.get_by_tg_id(user_id)
        lang = get_user_language(user)
        
        # Clear the cart
        success = await cart_service.clear_cart(user_id)
        
        if success:
            text = translator.get_text("cart.cleared", lang)
            keyboard = get_main_menu_keyboard(user)
            await safe_edit_message(callback_query, text, keyboard)
            await callback_query.answer("🗑️ Cart cleared!")
        else:
            await callback_query.answer("❌ Failed to clear cart")
        
    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        await callback_query.answer("❌ An error occurred")


async def cart_item_action_callback(client: Client, callback_query: CallbackQuery):
    """Handle cart item actions (remove, increase, decrease)."""
    try:
        user_id = callback_query.from_user.id
        user = await user_repo.get_by_tg_id(user_id)
        lang = get_user_language(user)
        
        data = callback_query.data
        action, item_id = data.split(":", 1)
        
        if action == "cart_remove":
            # Remove item from cart
            success = await cart_service.remove_item(user_id, item_id)
            if success:
                await callback_query.answer("🗑️ Item removed from cart")
                # Refresh cart display
                await show_cart(callback_query, user)
            else:
                await callback_query.answer("❌ Failed to remove item")
                
        elif action == "cart_increase":
            # Get current cart to find the item
            cart = await cart_service.get_or_create_cart(user_id)
            cart_item = None
            for item in cart.items:
                if item.product_id == item_id:
                    cart_item = item
                    break
            
            if cart_item:
                new_quantity = cart_item.quantity + 1
                success = await cart_service.update_item_quantity(user_id, item_id, new_quantity)
                if success:
                    await callback_query.answer(f"➕ Quantity increased to {new_quantity}")
                    await show_cart(callback_query, user)
                else:
                    await callback_query.answer("❌ Failed to increase quantity")
            else:
                await callback_query.answer("❌ Item not found")
                
        elif action == "cart_decrease":
            # Get current cart to find the item
            cart = await cart_service.get_or_create_cart(user_id)
            cart_item = None
            for item in cart.items:
                if item.product_id == item_id:
                    cart_item = item
                    break
            
            if cart_item:
                if cart_item.quantity > 1:
                    new_quantity = cart_item.quantity - 1
                    success = await cart_service.update_item_quantity(user_id, item_id, new_quantity)
                    if success:
                        await callback_query.answer(f"➖ Quantity decreased to {new_quantity}")
                        await show_cart(callback_query, user)
                    else:
                        await callback_query.answer("❌ Failed to decrease quantity")
                else:
                    # Remove item if quantity would become 0
                    success = await cart_service.remove_item(user_id, item_id)
                    if success:
                        await callback_query.answer("🗑️ Item removed (quantity was 1)")
                        await show_cart(callback_query, user)
                    else:
                        await callback_query.answer("❌ Failed to remove item")
            else:
                await callback_query.answer("❌ Item not found")
        
    except Exception as e:
        logger.error(f"Error in cart item action: {e}")
        await callback_query.answer("❌ An error occurred")
