"""Main menu keyboards."""

from pyrogram.types import InlineKeyboardMarkup
from .base import BaseKeyboardBuilder
from app.i18n import _, get_user_language


def get_main_menu_keyboard(user=None) -> InlineKeyboardMarkup:
    """Get main menu keyboard."""
    lang = get_user_language(user)
    
    builder = BaseKeyboardBuilder()
    
    # First row - Order Products and Check Stock
    builder.add_buttons_row([
        {"text": _("start.order_products", lang), "callback_data": "order_products"},
        {"text": _("start.check_stock", lang), "callback_data": "check_stock"}
    ])
    
    # Second row - Support and Crypto Deposit
    builder.add_buttons_row([
        {"text": _("start.support", lang), "callback_data": "support"},
        {"text": "💳 Crypto Deposit", "callback_data": "crypto_deposit"}
    ])
    
    # Third row - Language and Cart
    builder.add_buttons_row([
        {"text": _("start.language", lang), "callback_data": "language"},
        {"text": _("start.my_cart", lang), "callback_data": "my_cart"}
    ])
    
    return builder.build()


def get_city_selection_keyboard(user=None) -> InlineKeyboardMarkup:
    """Get city selection keyboard."""
    lang = get_user_language(user)
    
    builder = BaseKeyboardBuilder()
    
    builder.add_button(
        _("location.belgrade", lang),
        "city:Belgrade"
    )
    builder.add_button(
        _("location.novi_sad", lang),
        "city:Novi Sad"
    )
    builder.add_button(
        _("location.pancevo", lang),
        "city:Pančevo"
    )
    
    builder.add_back_button("back_to_main")
    
    return builder.build()


def get_area_selection_keyboard(city: str, user=None) -> InlineKeyboardMarkup:
    """Get area selection keyboard for a city."""
    lang = get_user_language(user)
    
    builder = BaseKeyboardBuilder()
    
    if city == "Belgrade":
        areas = [
            "Vracar", "Novi Beograd", "Stari grad", "Zvezdara",
            "Vozdovac", "Konjarnik", "Savski venac", "Banovo brdo",
            "Mirijevo", "Zemun", "Ada Ciganlija", "Palilula",
            "Senjak", "Karaburma", "Borca"
        ]
        # Split into rows of 2
        for i in range(0, len(areas), 2):
            row_areas = areas[i:i+2]
            row = []
            for area in row_areas:
                row.append({
                    "text": area,
                    "callback_data": f"area:{city}:{area}"
                })
            builder.add_buttons_row(row)
    
    elif city == "Novi Sad":
        areas = ["Centar", "Podbara", "Petrovaradin", "Detelinara"]
        for i in range(0, len(areas), 2):
            row_areas = areas[i:i+2]
            row = []
            for area in row_areas:
                row.append({
                    "text": area,
                    "callback_data": f"area:{city}:{area}"
                })
            builder.add_buttons_row(row)
    
    elif city == "Pančevo":
        builder.add_button("Centar", f"area:{city}:Centar")
    
    builder.add_back_button("back_to_cities")
    
    return builder.build()


def get_language_keyboard(user=None) -> InlineKeyboardMarkup:
    """Get language selection keyboard."""
    builder = BaseKeyboardBuilder()
    
    builder.add_button("🇺🇸 English", "lang:en")
    builder.add_button("🇷🇸 Serbian", "lang:sr")
    builder.add_button("🇷🇺 Russian", "lang:ru")
    
    builder.add_back_button("back_to_main")
    
    return builder.build()

