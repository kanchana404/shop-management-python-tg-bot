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
    get_crypto_selection_keyboard,
    get_deposit_confirmation_keyboard
)
from app.i18n import translator, get_user_language
from app.utils.rate_limiter import rate_limiter
from app.utils.validators import validate_amount
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
            
        elif data == "check_stock":
            text = translator.get_text("location.choose_city", lang)
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
            
        elif data == "back_to_main":
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
        products = await product_repo.get_products_by_location(city_enum, area_enum)
        
        if not products:
            text = translator.get_text("products.no_products", lang)
            keyboard = get_area_selection_keyboard(city, user)
            await callback_query.edit_message_text(text, reply_markup=keyboard)
        else:
            text = f"{translator.get_text('products.title', lang)} - {city}, {area}"
            is_stock_check = "stock" in callback_query.message.text.lower()
            keyboard = get_products_keyboard(products, city, area, 1, 1, is_stock_check, user)
            
            # Create products listing text
            products_text = text + "\n\n"
            for product in products[:5]:  # Show first 5 products
                products_text += f"🛒 **{product.name}**\n"
                products_text += f"💰 {product.price:.2f} EUR\n"
                products_text += f"📦 {product.quantity} available\n"
                products_text += f"📝 {product.description[:100]}...\n\n"
            
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
        lang = get_user_language(user)
        cart_summary = await cart_service.get_cart_summary(user.tg_id)
        
        if not cart_summary["items"]:
            text = translator.get_text("cart.empty", lang)
            keyboard = get_main_menu_keyboard(user)
            await callback_query.edit_message_text(text, reply_markup=keyboard)
            return
        
        # Build cart text
        text = f"{translator.get_text('cart.title', lang)}\n\n"
        text += f"💰 {translator.get_text('cart.balance', lang)}: {user.balance:.2f} EUR\n\n"
        
        for item in cart_summary["items"]:
            text += f"🛒 {item.product_name}\n"
            text += f"   💰 {item.price:.2f} EUR x {item.quantity} = {item.total_price:.2f} EUR\n\n"
        
        text += f"📦 {translator.get_text('cart.items', lang)}: {cart_summary['items_count']}\n"
        text += f"💵 {translator.get_text('cart.total', lang)}: {cart_summary['total_amount']:.2f} EUR"
        
        keyboard = get_cart_keyboard(user)
        await safe_edit_message(callback_query, text, keyboard)
        
    except Exception as e:
        logger.error(f"Error showing cart: {e}")
        await callback_query.answer("❌ An error occurred")


async def checkout_callback(client: Client, callback_query: CallbackQuery):
    """Handle checkout."""
    try:
        user_id = callback_query.from_user.id
        user = await user_repo.get_by_tg_id(user_id)
        lang = get_user_language(user)
        
        # Create order from cart
        order = await order_service.create_order_from_cart(user)
        
        if not order:
            cart_summary = await cart_service.get_cart_summary(user_id)
            if not cart_summary["items"]:
                text = translator.get_text("cart.empty", lang)
            elif user.balance < cart_summary["total_amount"]:
                text = translator.get_text("cart.insufficient_balance", lang)
            else:
                text = "❌ An error occurred"
            
            await callback_query.answer(text)
            return
        
        # Success message with payment options
        text = translator.get_text("cart.checkout_success", lang)
        text += f"\n\n📋 Order ID: {order.id}"
        text += f"\n💵 Total: {order.total_amount:.2f} EUR"
        text += f"\n\n💳 **Payment Options:**"
        text += f"\n• Balance: {user.balance:.2f} EUR"
        text += f"\n• Crypto Payment (USDT)"
        
        # Create payment keyboard
        from app.keyboards.crypto import get_crypto_payment_keyboard
        keyboard = get_crypto_payment_keyboard(str(order.id))
        
        await safe_edit_message(callback_query, text, keyboard)
        await callback_query.answer()
        
        # Send order details to user
        order_details = f"📦 **Order Details**\n\n"
        for item in order.items:
            order_details += f"🛒 {item.product_name}\n"
            order_details += f"   💰 {item.price:.2f} EUR x {item.quantity}\n\n"
        
        await client.send_message(user_id, order_details)
        
    except Exception as e:
        logger.error(f"Error in checkout: {e}")
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
