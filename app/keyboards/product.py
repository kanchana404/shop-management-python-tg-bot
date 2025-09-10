"""Product-related keyboards."""

from typing import List
from pyrogram.types import InlineKeyboardMarkup
from .base import BaseKeyboardBuilder
from app.models import Product
from app.i18n import _, get_user_language


def get_products_keyboard(
    products: List[Product],
    city: str,
    area: str,
    current_page: int = 1,
    total_pages: int = 1,
    is_stock_check: bool = False,
    user=None
) -> InlineKeyboardMarkup:
    """Get products listing keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    # Add to cart buttons for each product (all products shown are available)
    for product in products:
        # Simple available product button (no stock indicators since we pre-filter)
        button_text = f"🛒 {product.name}"
        
        # All products shown are available, so always use add_to_cart
        builder.add_button(
            button_text,
            f"add_to_cart:{product.id}"
        )
    
    # Add pagination if needed
    if total_pages > 1:
        callback_prefix = f"products_page:{city}:{area}"
        builder.add_pagination(current_page, total_pages, callback_prefix)
    
    # Back button
    builder.add_back_button(f"back_to_area:{city}")
    
    return builder.build()


def get_product_details_keyboard(
    product: Product,
    user=None,
    show_add_to_cart: bool = True
) -> InlineKeyboardMarkup:
    """Get product details keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    if show_add_to_cart and product.is_active:
        builder.add_button(
            _("products.add_to_cart", lang),
            f"add_to_cart:{product.id}"
        )
    
    builder.add_back_button("back_to_products")
    
    return builder.build()


def get_cart_keyboard(user=None) -> InlineKeyboardMarkup:
    """Get cart keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    # Checkout button
    builder.add_button(
        _("cart.checkout", lang),
        "checkout"
    )
    
    # Clear cart button
    builder.add_button(
        "🗑️ Clear Cart",
        "clear_cart"
    )
    
    builder.add_back_button("back_to_main")
    
    return builder.build()


def get_enhanced_cart_keyboard(user=None, cart_items=None) -> InlineKeyboardMarkup:
    """Get enhanced cart keyboard with individual item management."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    # Add item management buttons for each item
    if cart_items:
        for item in cart_items:
            # Item name with quantity
            item_text = f"📦 {item.product_name} ({item.quantity})"
            builder.add_button(item_text, f"cart_item_info:{item.product_id}")
            
            # Quantity controls in same row
            builder.add_buttons_row([
                {"text": "➖", "callback_data": f"cart_decrease:{item.product_id}"},
                {"text": f"🗑️", "callback_data": f"cart_remove:{item.product_id}"},
                {"text": "➕", "callback_data": f"cart_increase:{item.product_id}"}
            ])
    
    # Separator
    builder.add_button("─" * 20, "separator")
    
    # Main action buttons
    builder.add_button(
        _("cart.checkout", lang),
        "checkout"
    )
    
    # Clear cart button
    builder.add_button(
        "🗑️ Clear All Items",
        "clear_cart"
    )
    
    builder.add_back_button("back_to_main")
    
    return builder.build()


def get_cart_item_keyboard(item_id: str, user=None) -> InlineKeyboardMarkup:
    """Get individual cart item keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    # Quantity controls
    builder.add_buttons_row([
        {"text": "➖", "callback_data": f"cart_decrease:{item_id}"},
        {"text": "➕", "callback_data": f"cart_increase:{item_id}"}
    ])
    
    # Remove item
    builder.add_button(
        _("common.delete", lang),
        f"cart_remove:{item_id}"
    )
    
    return builder.build()





