"""Crypto payment handlers for the bot."""

import json
import logging
from typing import Optional
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from app.db.user_repository import user_repo
from app.services import crypto_pay_service, order_service
from app.keyboards import get_crypto_asset_keyboard, get_crypto_deposit_keyboard, get_main_menu_keyboard
from app.i18n import translator, get_user_language
from app.utils.rate_limiter import rate_limiter
from app.utils.validators import validate_amount

logger = logging.getLogger(__name__)


@rate_limiter
async def crypto_deposit_callback(client: Client, callback_query: CallbackQuery):
    """Handle crypto deposit selection."""
    try:
        logger.info(f"Crypto deposit callback triggered: {callback_query.data}")
        print(f"\n💳 CRYPTO DEPOSIT CALLBACK: '{callback_query.data}' from user {callback_query.from_user.id}")
        user_id = callback_query.from_user.id
        user = await user_repo.get_by_tg_id(user_id)
        lang = get_user_language(user)
        
        try:
            text = translator.get_text("crypto.choose_asset", lang)
        except:
            text = "💳 Choose cryptocurrency for deposit:"
        
        keyboard = get_crypto_asset_keyboard(user)
        
        logger.info("Updating message with crypto selection keyboard")
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
        logger.info("Crypto deposit callback completed successfully")
        
    except Exception as e:
        logger.error(f"Error in crypto deposit callback: {e}")
        await callback_query.answer("❌ An error occurred")


@rate_limiter
async def crypto_asset_selection_callback(client: Client, callback_query: CallbackQuery):
    """Handle crypto asset selection for deposit."""
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        logger.info(f"Crypto asset selection callback triggered: {data}")
        print(f"\n🪙 CRYPTO ASSET CALLBACK: '{data}' from user {user_id}")
        
        if not data.startswith("crypto_asset:"):
            logger.warning(f"Invalid crypto asset callback data: {data}")
            return
        
        asset = data.split(":", 1)[1]
        logger.info(f"Selected asset: {asset}")
        
        user = await user_repo.get_by_tg_id(user_id)
        lang = get_user_language(user)
        
        # Check if crypto pay is configured
        if not crypto_pay_service.token:
            logger.info("Crypto payments not configured, showing error message")
            await callback_query.answer("❌ Crypto payments not configured")
            await callback_query.edit_message_text(
                "❌ **Crypto payments are not configured**\n\n"
                "Please contact support to enable cryptocurrency payments.",
                reply_markup=get_main_menu_keyboard(user)
            )
            return
        
        # Create text for amount input
        try:
            text = translator.get_text("crypto.enter_amount", lang, asset=asset)
        except Exception as e:
            logger.warning(f"Translation failed: {e}")
            text = f"💰 Enter amount for {asset} deposit:"
        
        text += f"\n\n💡 Supported: {asset}"
        text += f"\n💰 Minimum: 1 {asset}"
        text += f"\n💳 Maximum: 10000 {asset}"
        text += f"\n\n📝 **Please reply to this message with the amount you want to deposit.**"
        
        # Create a simple inline keyboard to go back
        from app.keyboards.base import BaseKeyboardBuilder
        keyboard = BaseKeyboardBuilder()
        keyboard.add_back_button("back_to_main")
        
        logger.info(f"Updating message with asset selection for {asset}")
        await callback_query.edit_message_text(text, reply_markup=keyboard.build())
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in crypto asset selection: {e}")
        await callback_query.answer("❌ An error occurred")


@rate_limiter
async def crypto_deposit_amount_handler(client: Client, message: Message):
    """Handle crypto deposit amount input."""
    try:
        user_id = message.from_user.id
        user = await user_repo.get_by_tg_id(user_id)
        lang = get_user_language(user)
        
        print(f"\n💰 AMOUNT INPUT DEBUG:")
        print(f"   User: {user.first_name if user else 'Unknown'} - ID: {user_id}")
        print(f"   Message: '{message.text}'")
        print(f"   Is Reply: {message.reply_to_message is not None}")
        if message.reply_to_message:
            print(f"   Reply Text: '{message.reply_to_message.text[:50]}...'")
            print(f"   Contains 'crypto': {'crypto' in message.reply_to_message.text.lower()}")
        
        # Ignore commands (messages starting with /)
        if message.text.startswith('/'):
            print(f"   ❌ COMMAND DETECTED - IGNORING")
            return
        
        # Check if this is a reply to a crypto deposit message
        is_crypto_reply = (message.reply_to_message and "crypto" in message.reply_to_message.text.lower())
        
        # Only process if this is actually a reply to a crypto deposit message
        if not is_crypto_reply:
            print(f"   ❌ NOT A CRYPTO REPLY - IGNORING")
            return
        
        print(f"   ✅ PROCESSING AMOUNT INPUT")
        
        # Parse amount from message
        try:
            amount = float(message.text.strip())
        except ValueError:
            await message.reply_text("❌ Please enter a valid amount (e.g., 10.5)")
            return
        
        # Validate amount
        if amount < 1:
            await message.reply_text("❌ Minimum deposit amount is 1 USDT")
            return
        if amount > 10000:
            await message.reply_text("❌ Maximum deposit amount is 10,000 USDT")
            return
        
        # Check if crypto pay is configured
        if not crypto_pay_service.token:
            await message.reply_text("❌ Crypto payments are not configured. Please contact support.")
            return
        
        # Create deposit invoice
        try:
            invoice = await crypto_pay_service.create_deposit_invoice(
                user_id=user_id,
                amount=str(amount),
                asset="USDT",
                description=f"Deposit {amount} USDT to your account"
            )
            
            # Send payment link
            payment_text = f"💳 **Crypto Deposit Invoice**\n\n"
            payment_text += f"💰 Amount: {amount} USDT\n"
            payment_text += f"👤 User: {user.first_name}\n"
            payment_text += f"🆔 Invoice ID: `{invoice['invoice_id']}`\n\n"
            payment_text += "🔗 **Payment Link:**\n"
            payment_text += f"`{invoice['bot_invoice_url']}`\n\n"
            payment_text += "📱 **Or use Mini App:**\n"
            payment_text += f"`{invoice['mini_app_invoice_url']}`\n\n"
            payment_text += "⏰ **Expires in:** 1 hour\n"
            payment_text += "💡 **Status:** Waiting for payment"
            
            keyboard = get_crypto_deposit_keyboard(user)
            
            await message.reply_text(payment_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error creating crypto deposit invoice: {e}")
            await message.reply_text("❌ Failed to create payment invoice. Please try again.")
        
    except Exception as e:
        logger.error(f"Error in crypto deposit amount handler: {e}")
        await message.reply_text("❌ An error occurred")


@rate_limiter
async def crypto_payment_callback(client: Client, callback_query: CallbackQuery):
    """Handle crypto payment for orders."""
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        if not data.startswith("crypto_pay:"):
            return
        
        order_id = data.split(":", 1)[1]
        user = await user_repo.get_by_tg_id(user_id)
        lang = get_user_language(user)
        
        # Get order details
        order = await order_service.get_order_by_id(order_id)
        if not order:
            await callback_query.answer("❌ Order not found")
            return
        
        if order.user_id != user_id:
            await callback_query.answer("❌ Access denied")
            return
        
        # Create payment invoice
        try:
            invoice = await crypto_pay_service.create_order_invoice(
                user_id=user_id,
                order_id=order_id,
                amount=str(order.total_amount),
                asset="USDT",
                description=f"Payment for order #{order_id}"
            )
            
            # Send payment link
            payment_text = f"💳 **Order Payment Invoice**\n\n"
            payment_text += f"📦 Order ID: `{order_id}`\n"
            payment_text += f"💰 Total: {order.total_amount} USDT\n"
            payment_text += f"👤 Customer: {user.first_name}\n"
            payment_text += f"🆔 Invoice ID: `{invoice['invoice_id']}`\n\n"
            payment_text += "🔗 **Payment Link:**\n"
            payment_text += f"`{invoice['bot_invoice_url']}`\n\n"
            payment_text += "📱 **Or use Mini App:**\n"
            payment_text += f"`{invoice['mini_app_invoice_url']}`\n\n"
            payment_text += "⏰ **Expires in:** 30 minutes\n"
            payment_text += "💡 **Status:** Waiting for payment"
            
            keyboard = get_crypto_deposit_keyboard(user)
            
            await callback_query.edit_message_text(payment_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error creating crypto payment invoice: {e}")
            await callback_query.answer("❌ Failed to create payment invoice")
        
    except Exception as e:
        logger.error(f"Error in crypto payment callback: {e}")
        await callback_query.answer("❌ An error occurred")


@rate_limiter
async def crypto_balance_callback(client: Client, callback_query: CallbackQuery):
    """Show crypto balance."""
    try:
        user_id = callback_query.from_user.id
        user = await user_repo.get_by_tg_id(user_id)
        lang = get_user_language(user)
        
        # Get app balance
        try:
            balance = await crypto_pay_service.get_balance()
            
            balance_text = f"💰 **Crypto Balance**\n\n"
            
            for asset_balance in balance:
                currency = asset_balance.get('currency_code', 'Unknown')
                available = asset_balance.get('available', '0')
                onhold = asset_balance.get('onhold', '0')
                
                balance_text += f"**{currency}:**\n"
                balance_text += f"  💵 Available: {available}\n"
                balance_text += f"  🔒 On Hold: {onhold}\n\n"
            
            if not balance:
                balance_text += "❌ No balance information available"
            
            from app.keyboards.base import BaseKeyboardBuilder
            keyboard = BaseKeyboardBuilder()
            keyboard.add_back_button("back_to_main")
            
            await callback_query.edit_message_text(balance_text, reply_markup=keyboard.build())
            
        except Exception as e:
            logger.error(f"Error getting crypto balance: {e}")
            await callback_query.answer("❌ Failed to get balance information")
        
    except Exception as e:
        logger.error(f"Error in crypto balance callback: {e}")
        await callback_query.answer("❌ An error occurred")


@rate_limiter
async def crypto_rates_callback(client: Client, callback_query: CallbackQuery):
    """Show crypto exchange rates."""
    try:
        user_id = callback_query.from_user.id
        user = await user_repo.get_by_tg_id(user_id)
        lang = get_user_language(user)
        
        # Get exchange rates
        try:
            rates = await crypto_pay_service.get_exchange_rates()
            
            rates_text = f"📊 **Exchange Rates**\n\n"
            
            # Filter for USD rates
            usd_rates = [rate for rate in rates if rate.get('target') == 'USD']
            
            for rate in usd_rates[:10]:  # Show first 10 rates
                source = rate.get('source', 'Unknown')
                rate_value = rate.get('rate', '0')
                is_valid = rate.get('is_valid', False)
                
                status = "✅" if is_valid else "⚠️"
                rates_text += f"{status} **{source}/USD:** {rate_value}\n"
            
            if not usd_rates:
                rates_text += "❌ No exchange rates available"
            
            from app.keyboards.base import BaseKeyboardBuilder
            keyboard = BaseKeyboardBuilder()
            keyboard.add_back_button("back_to_main")
            
            await callback_query.edit_message_text(rates_text, reply_markup=keyboard.build())
            
        except Exception as e:
            logger.error(f"Error getting crypto rates: {e}")
            await callback_query.answer("❌ Failed to get exchange rates")
        
    except Exception as e:
        logger.error(f"Error in crypto rates callback: {e}")
        await callback_query.answer("❌ An error occurred")


async def handle_crypto_webhook(webhook_data: dict) -> bool:
    """Handle Crypto Pay webhook updates."""
    try:
        update_type = webhook_data.get('update_type')
        
        if update_type == 'invoice_paid':
            payload = webhook_data.get('payload', {})
            
            # Extract payment information
            invoice_id = payload.get('invoice_id')
            status = payload.get('status')
            amount = payload.get('amount')
            asset = payload.get('asset')
            payload_data = payload.get('payload')
            
            if status == 'paid' and payload_data:
                try:
                    # Parse payload data
                    payment_info = json.loads(payload_data)
                    user_id = payment_info.get('user_id')
                    payment_type = payment_info.get('type')
                    
                    if payment_type == 'deposit':
                        # Handle deposit
                        await handle_crypto_deposit(user_id, amount, asset, invoice_id)
                    elif payment_type == 'order':
                        # Handle order payment
                        order_id = payment_info.get('order_id')
                        await handle_crypto_order_payment(user_id, order_id, amount, asset, invoice_id)
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid payload data in webhook: {payload_data}")
            
            logger.info(f"Crypto Pay webhook processed: {update_type} - Invoice {invoice_id}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error handling crypto webhook: {e}")
        return False


async def handle_crypto_deposit(user_id: int, amount: str, asset: str, invoice_id: int):
    """Handle successful crypto deposit."""
    try:
        # Update user balance
        user = await user_repo.get_by_tg_id(user_id)
        if user:
            # Convert crypto amount to EUR (you might want to use exchange rates)
            # For now, we'll use a simple conversion
            eur_amount = float(amount)  # Assuming 1:1 conversion for USDT
            
            user.balance += eur_amount
            await user_repo.update_user(user)
            
            # Send confirmation message
            try:
                from app.bot import bot
                await bot.send_message(
                    user_id,
                    f"✅ **Deposit Successful!**\n\n"
                    f"💰 Amount: {amount} {asset}\n"
                    f"💶 Added to balance: {eur_amount:.2f} EUR\n"
                    f"💳 New balance: {user.balance:.2f} EUR\n"
                    f"🆔 Invoice ID: {invoice_id}"
                )
            except ImportError:
                logger.warning("Bot not available for sending confirmation message")
            except Exception as e:
                logger.error(f"Error sending confirmation message: {e}")
            
            logger.info(f"Crypto deposit processed: User {user_id}, Amount {amount} {asset}")
        
    except Exception as e:
        logger.error(f"Error handling crypto deposit: {e}")


async def handle_crypto_order_payment(user_id: int, order_id: str, amount: str, asset: str, invoice_id: int):
    """Handle successful crypto order payment."""
    try:
        # Update order status
        order = await order_service.get_order_by_id(order_id)
        if order and order.user_id == user_id:
            # Mark order as paid
            order.status = "paid"
            order.payment_method = f"crypto_{asset.lower()}"
            order.payment_id = str(invoice_id)
            await order_service.update_order(order)
            
            # Send confirmation message
            try:
                from app.bot import bot
                await bot.send_message(
                    user_id,
                    f"✅ **Order Payment Successful!**\n\n"
                    f"📦 Order ID: {order_id}\n"
                    f"💰 Paid: {amount} {asset}\n"
                    f"💶 Total: {order.total_amount} EUR\n"
                    f"🆔 Invoice ID: {invoice_id}\n\n"
                    f"🚚 Your order is being processed!"
                )
            except ImportError:
                logger.warning("Bot not available for sending confirmation message")
            except Exception as e:
                logger.error(f"Error sending confirmation message: {e}")
            
            logger.info(f"Crypto order payment processed: Order {order_id}, Amount {amount} {asset}")
        
    except Exception as e:
        logger.error(f"Error handling crypto order payment: {e}")


# Message handler for amount input
async def handle_amount_input(client: Client, message: Message):
    """Handle amount input for crypto deposits."""
    try:
        # Check if this is a reply to a crypto deposit message
        if message.reply_to_message and "crypto" in message.reply_to_message.text.lower():
            await crypto_deposit_amount_handler(client, message)
    except Exception as e:
        logger.error(f"Error handling amount input: {e}")
