"""Crypto payment keyboards."""

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.keyboards.base import BaseKeyboardBuilder


def get_crypto_selection_keyboard(user) -> InlineKeyboardMarkup:
    """Get crypto asset selection keyboard."""
    builder = BaseKeyboardBuilder()
    
    # Supported crypto assets
    assets = [
        ("USDT", "USDT"),
        ("TON", "TON"),
        ("BTC", "Bitcoin"),
        ("ETH", "Ethereum"),
        ("LTC", "Litecoin"),
        ("BNB", "BNB"),
        ("TRX", "TRON"),
        ("USDC", "USDC")
    ]
    
    # Add asset buttons
    for asset_code, asset_name in assets:
        builder.add_button(
            text=f"{asset_name} ({asset_code})",
            callback_data=f"crypto_asset:{asset_code}"
        )
    
    # Add back button
    builder.add_back_button("back_to_main")
    
    return builder.build()


def get_deposit_confirmation_keyboard(user) -> InlineKeyboardMarkup:
    """Get deposit confirmation keyboard."""
    builder = BaseKeyboardBuilder()
    
    # Add action buttons
    builder.add_button("💰 Check Balance", "crypto_balance")
    builder.add_button("📊 Exchange Rates", "crypto_rates")
    builder.add_button("📋 My Orders", "my_orders")
    builder.add_button("💳 New Deposit", "crypto_deposit")
    
    # Add back button
    builder.add_back_button("back_to_main")
    
    return builder.build()


def get_crypto_payment_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Get crypto payment keyboard for orders."""
    builder = BaseKeyboardBuilder()
    
    # Add payment button
    builder.add_button(
        text="💳 Pay with Crypto",
        callback_data=f"crypto_pay:{order_id}"
    )
    
    # Add back button
    builder.add_back_button("back_to_main")
    
    return builder.build()


def get_crypto_balance_keyboard() -> InlineKeyboardMarkup:
    """Get crypto balance keyboard."""
    builder = BaseKeyboardBuilder()
    
    # Add action buttons
    builder.add_button("📊 Exchange Rates", "crypto_rates")
    builder.add_button("💳 New Deposit", "crypto_deposit")
    builder.add_button("📋 My Orders", "my_orders")
    
    # Add back button
    builder.add_back_button("back_to_main")
    
    return builder.build()


def get_crypto_rates_keyboard() -> InlineKeyboardMarkup:
    """Get crypto rates keyboard."""
    builder = BaseKeyboardBuilder()
    
    # Add action buttons
    builder.add_button("💰 Check Balance", "crypto_balance")
    builder.add_button("💳 New Deposit", "crypto_deposit")
    builder.add_button("📋 My Orders", "my_orders")
    
    # Add back button
    builder.add_back_button("back_to_main")
    
    return builder.build()


