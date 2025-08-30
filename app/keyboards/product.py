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
    
    # Add to cart buttons for each product
    for product in products:
        button_text = f"➕ {product.name}"
        if product.quantity == 0:
            button_text = f"❌ {product.name}"
        elif product.quantity <= 5:
            button_text = f"⚠️ {product.name}"
        
        callback_prefix = "stock" if is_stock_check else "add_to_cart"
        builder.add_button(
            button_text,
            f"{callback_prefix}:{product.id}" if product.quantity > 0 else "out_of_stock"
        )
    
    # Add pagination if needed
    if total_pages > 1:
        callback_prefix = f"products_page:{city}:{area}"
        if is_stock_check:
            callback_prefix = f"stock_page:{city}:{area}"
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
    
    if show_add_to_cart and product.quantity > 0:
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



