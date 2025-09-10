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
from app.utils.user_state import user_state_manager, UserStates
from app.config.crypto_limits import get_crypto_minimum, get_crypto_maximum, validate_crypto_amount, format_crypto_minimum

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
        
        # Check and send balance notification if user was inactive
        show_balance = await user_activity_tracker.should_show_balance(user_id)
        await user_activity_tracker.update_activity(user_id)
        
        if show_balance:
            from app.services.balance_service import balance_service
            balance_text = await balance_service.get_quick_balance_notification(user_id)
            if balance_text:
                await callback_query.message.reply_text(balance_text)
                logger.info(f"Sent balance notification to user {user_id}")
        
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
        text += f"\n💰 Minimum: {format_crypto_minimum(asset)}"
        text += f"\n💳 Maximum: {get_crypto_maximum(asset)} {asset}"
        text += f"\n\n📝 **Please send the amount you want to deposit.**"
        
        # Set user state for amount input
        await user_state_manager.set_state(
            user_id, 
            UserStates.CRYPTO_DEPOSIT_AMOUNT_INPUT, 
            {'asset': asset}, 
            timeout_minutes=15
        )
        
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
        print(f"   User State: {await user_state_manager.get_state(user_id)}")
        
        # Ignore commands (messages starting with /)
        if message.text.startswith('/'):
            print(f"   ❌ COMMAND DETECTED - IGNORING")
            return
        
        # Check if user is in crypto deposit amount input state
        is_crypto_amount_state = await user_state_manager.is_in_state(user_id, UserStates.CRYPTO_DEPOSIT_AMOUNT_INPUT)
        
        if not is_crypto_amount_state:
            print(f"   ❌ USER NOT IN CRYPTO AMOUNT INPUT STATE - IGNORING")
            return
        
        print(f"   ✅ PROCESSING AMOUNT INPUT")
        
        # Get the asset from state data
        state_data = await user_state_manager.get_state_data(user_id)
        asset = state_data.get('asset', 'USDT') if state_data else 'USDT'
        print(f"   💱 Asset: {asset}")
        
        # Parse amount from message
        try:
            amount = float(message.text.strip())
        except ValueError:
            await message.reply_text("❌ Please enter a valid amount (e.g., 10.5)")
            return
        
        # Validate amount using realistic crypto minimums
        is_valid, error_message = validate_crypto_amount(amount, asset)
        if not is_valid:
            await message.reply_text(error_message)
            return
        
        # Clear user state since we're processing the amount
        await user_state_manager.clear_state(user_id)
        
        # Check if crypto pay is configured
        if not crypto_pay_service.token:
            await message.reply_text("❌ Crypto payments are not configured. Please contact support.")
            return
        
        # Create deposit invoice
        try:
            invoice = await crypto_pay_service.create_deposit_invoice(
                user_id=user_id,
                amount=str(amount),
                asset=asset,
                description=f"Deposit {amount} {asset} to your account"
            )
            
            # Send payment link
            payment_text = f"💳 **Crypto Deposit Invoice**\n\n"
            payment_text += f"💰 Amount: {amount} {asset}\n"
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
    """Handle Crypto Pay webhook updates with proper invoice tracking."""
    try:
        # Extract top-level webhook data
        update_id = webhook_data.get('update_id')
        update_type = webhook_data.get('update_type')
        request_date = webhook_data.get('request_date')
        
        logger.info(f"Processing webhook {update_id}: {update_type} at {request_date}")
        
        if update_type == 'invoice_paid':
            # Extract Invoice object from payload according to API docs
            invoice_data = webhook_data.get('payload', {})
            
            # Extract all Invoice fields according to API documentation
            invoice_id = invoice_data.get('invoice_id')
            invoice_hash = invoice_data.get('hash')
            currency_type = invoice_data.get('currency_type', 'crypto')
            asset = invoice_data.get('asset')
            fiat = invoice_data.get('fiat')
            amount = invoice_data.get('amount')
            status = invoice_data.get('status')
            
            # Extract payment details (only available for paid invoices)
            paid_asset = invoice_data.get('paid_asset', asset)  # Fallback to original asset
            paid_amount = invoice_data.get('paid_amount', amount)  # Fallback to original amount
            paid_usd_rate = invoice_data.get('paid_usd_rate')
            paid_fiat_rate = invoice_data.get('paid_fiat_rate')
            
            # Extract fee information
            fee_asset = invoice_data.get('fee_asset')
            fee_amount = invoice_data.get('fee_amount', 0)
            
            # Extract timestamps
            created_at = invoice_data.get('created_at')
            paid_at = invoice_data.get('paid_at')
            
            # Extract swap information (if applicable)
            swap_to = invoice_data.get('swap_to')
            is_swapped = invoice_data.get('is_swapped', False)
            swapped_to = invoice_data.get('swapped_to')
            swapped_rate = invoice_data.get('swapped_rate')
            swapped_output = invoice_data.get('swapped_output')
            
            logger.info(f"Invoice {invoice_id}: {paid_amount} {paid_asset} (original: {amount} {asset})")
            if is_swapped:
                logger.info(f"Swap detected: {swapped_output} {swapped_to} at rate {swapped_rate}")
            
            if status == 'paid' and invoice_id:
                try:
                    # Get stored invoice from database
                    from app.db.invoice_repository import invoice_repo
                    from datetime import datetime
                    
                    stored_invoice = await invoice_repo.get_by_invoice_id(invoice_id)
                    if not stored_invoice:
                        logger.error(f"Invoice {invoice_id} not found in database. Cannot process payment.")
                        return False
                    
                    logger.info(f"Found stored invoice: User {stored_invoice.user_id}, Type {stored_invoice.type}")
                    
                    # Use the actual paid amount and asset (important for swaps)
                    final_amount = swapped_output if is_swapped else paid_amount
                    final_asset = swapped_to if is_swapped else paid_asset
                    
                    # Mark invoice as paid in database
                    paid_at_datetime = None
                    if paid_at:
                        try:
                            paid_at_datetime = datetime.fromisoformat(paid_at.replace('Z', '+00:00'))
                        except:
                            paid_at_datetime = datetime.utcnow()
                    
                    updated_invoice = await invoice_repo.mark_as_paid(
                        invoice_id=invoice_id,
                        paid_amount=final_amount,
                        paid_asset=final_asset,
                        paid_usd_rate=paid_usd_rate,
                        fee_amount=fee_amount,
                        fee_asset=fee_asset,
                        is_swapped=is_swapped,
                        swapped_to=swapped_to,
                        swapped_amount=swapped_output,
                        swapped_rate=swapped_rate,
                        paid_at=paid_at_datetime
                    )
                    
                    if not updated_invoice:
                        logger.error(f"Failed to update invoice {invoice_id} status to paid")
                        return False
                    
                    logger.info(f"Invoice {invoice_id} marked as paid in database")
                    
                    # Process payment based on invoice type
                    if stored_invoice.type == 'deposit':
                        await handle_crypto_deposit_from_invoice(updated_invoice)
                    elif stored_invoice.type == 'order':
                        await handle_crypto_order_payment_from_invoice(updated_invoice)
                    else:
                        logger.error(f"Unknown invoice type: {stored_invoice.type}")
                        return False
                    
                except Exception as e:
                    logger.error(f"Error processing paid invoice {invoice_id}: {e}")
                    return False
            else:
                logger.warning(f"Invoice {invoice_id} not in paid status or missing invoice_id")
            
            logger.info(f"Crypto Pay webhook processed: {update_type} - Invoice {invoice_id}")
            return True
        
        logger.warning(f"Unhandled webhook type: {update_type}")
        return False
        
    except Exception as e:
        logger.error(f"Error handling crypto webhook: {e}")
        return False


async def handle_crypto_deposit_from_invoice(invoice) -> bool:
    """Handle crypto deposit using stored invoice data."""
    try:
        from app.db.user_repository import user_repo
        from app.db.user_deposits_repository import user_deposits_repo
        from app.bot import bot
        
        user_id = invoice.user_id
        final_amount = invoice.paid_amount or invoice.amount
        final_asset = invoice.paid_asset or invoice.asset
        
        logger.info(f"Processing deposit from invoice {invoice.invoice_id}: {final_amount} {final_asset} for user {user_id}")
        
        # Convert to balance (assuming 1:1 USDT ratio)
        balance_amount = float(final_amount)
        
        # Update user balance
        updated_user = await user_repo.update_balance(user_id, balance_amount)
        
        if updated_user:
            logger.info(f"Balance updated for user {user_id}: +{balance_amount} USDT (new balance: {updated_user.balance} USDT)")
            
            # Record deposit in user_deposits collection
            try:
                # Prepare swap details if applicable
                swapped_details = None
                if invoice.is_swapped:
                    swapped_details = {
                        "swapped_to": invoice.swapped_to,
                        "swapped_amount": invoice.swapped_amount,
                        "swapped_rate": invoice.swapped_rate
                    }
                
                # Add deposit transaction to user deposits tracking
                updated_deposits = await user_deposits_repo.add_deposit_transaction(
                    user_id=user_id,
                    invoice_id=invoice.invoice_id,
                    amount=invoice.amount,
                    asset=invoice.asset,
                    paid_amount=final_amount,
                    paid_asset=final_asset,
                    usd_rate=invoice.paid_usd_rate,
                    fee_amount=invoice.fee_amount,
                    fee_asset=invoice.fee_asset,
                    is_swapped=invoice.is_swapped,
                    swapped_details=swapped_details
                )
                
                if updated_deposits:
                    logger.info(f"Deposit recorded in user_deposits: User {user_id} now has {updated_deposits.total_deposits_count} deposits totaling {updated_deposits.total_deposited_usdt} USDT")
                else:
                    logger.error(f"Failed to record deposit in user_deposits for user {user_id}")
                
            except Exception as deposits_error:
                logger.error(f"Error recording deposit in user_deposits: {deposits_error}")
                # Continue with the process even if deposits tracking fails
            
            # Send detailed confirmation message
            try:
                if bot.active_clients:
                    client = bot.active_clients[0]
                    
                    # Get deposit summary for enhanced message
                    deposit_summary = await user_deposits_repo.get_user_deposit_summary(user_id)
                    
                    # Build detailed message
                    message = f"✅ **Deposit Successful!**\n\n"
                    message += f"💰 **Received:** {final_amount} {final_asset}\n"
                    message += f"🪙 **Added to wallet:** {balance_amount:.2f} USDT\n"
                    message += f"💳 **New balance:** {updated_user.balance:.2f} USDT\n"
                    
                    if invoice.amount != final_amount or invoice.asset != final_asset:
                        message += f"\n📊 **Original:** {invoice.amount} {invoice.asset}\n"
                        message += f"🔄 **Converted to:** {final_amount} {final_asset}\n"
                    
                    if invoice.paid_usd_rate:
                        message += f"💵 **USD Rate:** ${invoice.paid_usd_rate}\n"
                    
                    if invoice.fee_amount and invoice.fee_amount > 0:
                        message += f"💸 **Network Fee:** {invoice.fee_amount} {invoice.fee_asset or final_asset}\n"
                    
                    message += f"\n🆔 **Invoice ID:** {invoice.invoice_id}\n"
                    if invoice.paid_at:
                        message += f"⏰ **Paid at:** {invoice.paid_at.isoformat()}\n"
                    
                    # Add deposit statistics
                    if deposit_summary:
                        message += f"\n📈 **Your Deposit History:**\n"
                        message += f"• Total Deposits: {deposit_summary['total_deposits']}\n"
                        message += f"• Total Amount: {deposit_summary['total_amount']}\n"
                        if deposit_summary['total_fees'] != "0.00 USDT":
                            message += f"• Total Fees: {deposit_summary['total_fees']}\n"
                    
                    message += f"\n🎉 **Ready to shop!**"
                    
                    await client.send_message(user_id, message)
                    logger.info(f"Detailed confirmation sent to user {user_id}")
                else:
                    logger.warning("No active bot clients available for sending confirmation")
            except Exception as e:
                logger.error(f"Error sending confirmation message: {e}")
            
            logger.info(f"Crypto deposit processed successfully from invoice {invoice.invoice_id}")
            return True
        else:
            logger.error(f"Failed to update balance for user {user_id}")
            return False
        
    except Exception as e:
        logger.error(f"Error handling crypto deposit from invoice: {e}")
        return False


async def handle_crypto_order_payment_from_invoice(invoice) -> bool:
    """Handle crypto order payment using stored invoice data."""
    try:
        from app.services.order_service import order_service
        from app.bot import bot
        
        user_id = invoice.user_id
        order_id = invoice.order_id
        final_amount = invoice.paid_amount or invoice.amount
        final_asset = invoice.paid_asset or invoice.asset
        
        logger.info(f"Processing order payment from invoice {invoice.invoice_id}: Order {order_id}, {final_amount} {final_asset}")
        
        if not order_id:
            logger.error(f"No order_id found in invoice {invoice.invoice_id}")
            return False
        
        # Get and update order
        order = await order_service.get_order_by_id(order_id)
        if order and order.user_id == user_id:
            # Mark order as paid with detailed payment info
            order.status = "paid"
            order.payment_method = f"crypto_{final_asset.lower()}"
            order.payment_id = str(invoice.invoice_id)
            await order_service.update_order(order)
            
            # Send detailed confirmation message
            try:
                if bot.active_clients:
                    client = bot.active_clients[0]
                    
                    # Build detailed message
                    message = f"✅ **Order Payment Successful!**\n\n"
                    message += f"📦 **Order ID:** {order_id}\n"
                    message += f"💰 **Paid:** {final_amount} {final_asset}\n"
                    message += f"🪙 **Order Total:** {order.total_amount} USDT\n"
                    
                    if invoice.amount != final_amount or invoice.asset != final_asset:
                        message += f"\n📊 **Original:** {invoice.amount} {invoice.asset}\n"
                        message += f"🔄 **Converted to:** {final_amount} {final_asset}\n"
                    
                    if invoice.paid_usd_rate:
                        message += f"💵 **USD Rate:** ${invoice.paid_usd_rate}\n"
                    
                    if invoice.fee_amount and invoice.fee_amount > 0:
                        message += f"💸 **Network Fee:** {invoice.fee_amount} {invoice.fee_asset or final_asset}\n"
                    
                    message += f"\n🆔 **Invoice ID:** {invoice.invoice_id}\n"
                    if invoice.paid_at:
                        message += f"⏰ **Paid at:** {invoice.paid_at.isoformat()}\n"
                    
                    message += f"\n🚚 **Your order is being processed!**"
                    message += f"\n📧 You'll receive updates about your order status."
                    
                    await client.send_message(user_id, message)
                    logger.info(f"Detailed order confirmation sent to user {user_id}")
                else:
                    logger.warning("No active bot clients available for sending order confirmation")
            except Exception as e:
                logger.error(f"Error sending order confirmation message: {e}")
            
            logger.info(f"Crypto order payment processed successfully from invoice {invoice.invoice_id}")
            return True
        else:
            logger.error(f"Order not found or user mismatch: {order_id} for user {user_id}")
            return False
        
    except Exception as e:
        logger.error(f"Error handling crypto order payment from invoice: {e}")
        return False


async def handle_crypto_deposit(
    user_id: int, 
    amount: str, 
    asset: str, 
    invoice_id: int,
    original_amount: str = None,
    original_asset: str = None, 
    usd_rate: str = None,
    fee_amount: float = 0,
    fee_asset: str = None,
    paid_at: str = None
):
    """Handle successful crypto deposit with complete invoice data."""
    try:
        # Convert crypto amount to USDT equivalent for balance
        # Use actual received amount (important for swaps)
        received_amount = float(amount)
        
        logger.info(f"Processing deposit: {received_amount} {asset} for user {user_id}")
        if original_amount and original_asset and (original_amount != amount or original_asset != asset):
            logger.info(f"Original invoice: {original_amount} {original_asset} -> Received: {amount} {asset}")
        
        # Calculate fees
        net_amount = received_amount
        if fee_amount and fee_amount > 0:
            logger.info(f"Fee deducted: {fee_amount} {fee_asset or asset}")
            # Fees are already deducted by Crypto Pay, so we use the received amount
        
        # Update user balance (assuming 1:1 USDT to balance ratio)
        # In production, you might want to use exchange rates
        balance_amount = net_amount
        updated_user = await user_repo.update_balance(user_id, balance_amount)
        
        if updated_user:
            logger.info(f"Balance updated for user {user_id}: +{balance_amount} USDT (new balance: {updated_user.balance} USDT)")
            
            # Send detailed confirmation message
            try:
                from app.bot import bot
                
                if bot.active_clients:
                    client = bot.active_clients[0]
                    
                    # Build detailed message
                    message = f"✅ **Deposit Successful!**\n\n"
                    message += f"💰 **Received:** {amount} {asset}\n"
                    message += f"🪙 **Added to wallet:** {balance_amount:.2f} USDT\n"
                    message += f"💳 **New balance:** {updated_user.balance:.2f} USDT\n"
                    
                    if original_amount and (original_amount != amount or original_asset != asset):
                        message += f"\n📊 **Original:** {original_amount} {original_asset}\n"
                        message += f"🔄 **Converted to:** {amount} {asset}\n"
                    
                    if usd_rate:
                        message += f"💵 **USD Rate:** ${usd_rate}\n"
                    
                    if fee_amount and fee_amount > 0:
                        message += f"💸 **Network Fee:** {fee_amount} {fee_asset or asset}\n"
                    
                    message += f"\n🆔 **Invoice ID:** {invoice_id}\n"
                    if paid_at:
                        message += f"⏰ **Paid at:** {paid_at}\n"
                    
                    message += f"\n🎉 **Ready to shop!**"
                    
                    await client.send_message(user_id, message)
                    logger.info(f"Detailed confirmation sent to user {user_id}")
                else:
                    logger.warning("No active bot clients available for sending confirmation")
            except Exception as e:
                logger.error(f"Error sending confirmation message: {e}")
            
            logger.info(f"Crypto deposit processed successfully: User {user_id}, Final amount {amount} {asset}")
        else:
            logger.error(f"Failed to update balance for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling crypto deposit: {e}")


async def handle_crypto_order_payment(
    user_id: int, 
    order_id: str, 
    amount: str, 
    asset: str, 
    invoice_id: int,
    original_amount: str = None,
    original_asset: str = None,
    usd_rate: str = None,
    fee_amount: float = 0,
    fee_asset: str = None,
    paid_at: str = None
):
    """Handle successful crypto order payment with complete invoice data."""
    try:
        # Update order status
        order = await order_service.get_order_by_id(order_id)
        if order and order.user_id == user_id:
            # Mark order as paid with detailed payment info
            order.status = "paid"
            order.payment_method = f"crypto_{asset.lower()}"
            order.payment_id = str(invoice_id)
            await order_service.update_order(order)
            
            # Send detailed confirmation message
            try:
                from app.bot import bot
                
                if bot.active_clients:
                    client = bot.active_clients[0]
                    
                    # Build detailed message
                    message = f"✅ **Order Payment Successful!**\n\n"
                    message += f"📦 **Order ID:** {order_id}\n"
                    message += f"💰 **Paid:** {amount} {asset}\n"
                    message += f"🪙 **Order Total:** {order.total_amount} USDT\n"
                    
                    if original_amount and (original_amount != amount or original_asset != asset):
                        message += f"\n📊 **Original:** {original_amount} {original_asset}\n"
                        message += f"🔄 **Converted to:** {amount} {asset}\n"
                    
                    if usd_rate:
                        message += f"💵 **USD Rate:** ${usd_rate}\n"
                    
                    if fee_amount and fee_amount > 0:
                        message += f"💸 **Network Fee:** {fee_amount} {fee_asset or asset}\n"
                    
                    message += f"\n🆔 **Invoice ID:** {invoice_id}\n"
                    if paid_at:
                        message += f"⏰ **Paid at:** {paid_at}\n"
                    
                    message += f"\n🚚 **Your order is being processed!**"
                    message += f"\n📧 You'll receive updates about your order status."
                    
                    await client.send_message(user_id, message)
                    logger.info(f"Detailed order confirmation sent to user {user_id}")
                else:
                    logger.warning("No active bot clients available for sending order confirmation")
            except Exception as e:
                logger.error(f"Error sending order confirmation message: {e}")
            
            logger.info(f"Crypto order payment processed: Order {order_id}, Final amount {amount} {asset}")
        else:
            logger.error(f"Order not found or user mismatch: {order_id} for user {user_id}")
        
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
