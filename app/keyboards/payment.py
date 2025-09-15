"""Payment-related keyboards."""

from pyrogram.types import InlineKeyboardMarkup
from .base import BaseKeyboardBuilder
from app.models import CoinType
from app.i18n import _, get_user_language


def get_crypto_selection_keyboard(user=None) -> InlineKeyboardMarkup:
    """Get cryptocurrency selection keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    # Group coins by rows
    crypto_buttons = [
        [
            {"text": "USDT (TRC20)", "callback_data": f"crypto:{CoinType.USDT_TRC20.value}"},
            {"text": "USDT (BEP20)", "callback_data": f"crypto:{CoinType.USDT_BEP20.value}"}
        ],
        [
            {"text": "USDC (SOL)", "callback_data": f"crypto:{CoinType.USDC_SOL.value}"},
            {"text": "TON", "callback_data": f"crypto:{CoinType.TON.value}"}
        ],
        [
            {"text": "BTC", "callback_data": f"crypto:{CoinType.BTC.value}"},
            {"text": "LTC", "callback_data": f"crypto:{CoinType.LTC.value}"}
        ],
        [
            {"text": "ETH", "callback_data": f"crypto:{CoinType.ETH.value}"},
            {"text": "SOL", "callback_data": f"crypto:{CoinType.SOL.value}"}
        ],
        [
            {"text": "TRX", "callback_data": f"crypto:{CoinType.TRX.value}"},
            {"text": "BNB", "callback_data": f"crypto:{CoinType.BNB.value}"}
        ]
    ]
    
    for row in crypto_buttons:
        builder.add_buttons_row(row)
    
    builder.add_back_button("back_to_main")
    
    return builder.build()


def get_deposit_confirmation_keyboard(deposit_id: str, user=None) -> InlineKeyboardMarkup:
    """Get deposit confirmation keyboard."""
    lang = get_user_language(user)
    builder = BaseKeyboardBuilder()
    
    builder.add_button(
        "🔄 Check Status",
        f"check_deposit:{deposit_id}"
    )
    
    builder.add_button(
        "❌ Cancel Deposit",
        f"cancel_deposit:{deposit_id}"
    )
    
    builder.add_back_button("back_to_main")
    
    return builder.build()











