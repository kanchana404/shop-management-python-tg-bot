"""Balance conversion and display service."""

import logging
from typing import Optional
from app.db.user_repository import user_repo
from app.services.crypto_pay_service import crypto_pay_service

logger = logging.getLogger(__name__)

# Current EUR to USDT exchange rate (you can make this dynamic later)
EUR_TO_USDT_RATE = 1.08  # 1 EUR = ~1.08 USDT (approximate)


class BalanceService:
    """Service for balance conversion and display."""
    
    @staticmethod
    def usdt_to_eur(usdt_amount: float) -> float:
        """Convert USDT to EUR equivalent."""
        return usdt_amount / EUR_TO_USDT_RATE
    
    @staticmethod
    def eur_to_usdt(eur_amount: float) -> float:
        """Convert EUR to USDT equivalent."""
        return eur_amount * EUR_TO_USDT_RATE
    
    @staticmethod
    async def get_user_balance_eur(user_id: int) -> Optional[float]:
        """Get user's balance in EUR equivalent."""
        try:
            user = await user_repo.get_by_tg_id(user_id)
            if not user:
                return None
            
            # Convert USDT balance to EUR
            eur_balance = BalanceService.usdt_to_eur(user.balance)
            return round(eur_balance, 2)
            
        except Exception as e:
            logger.error(f"Error getting user balance in EUR: {e}")
            return None
    
    @staticmethod
    async def format_balance_display(user_id: int, show_detailed: bool = False) -> str:
        """Format user balance for display."""
        try:
            user = await user_repo.get_by_tg_id(user_id)
            if not user:
                return "❌ User not found"
            
            usdt_balance = user.balance
            eur_balance = BalanceService.usdt_to_eur(usdt_balance)
            
            if show_detailed:
                # Detailed balance display
                text = "💰 **Your Crypto Wallet Balance**\n"
                text += "═" * 30 + "\n\n"
                text += "┌─────────────────────────┐\n"
                text += f"│ 💵 **EUR Balance**      │\n"
                text += f"│ **€{eur_balance:.2f}**            │\n"
                text += "└─────────────────────────┘\n\n"
                text += "┌─────────────────────────┐\n"
                text += f"│ 🪙 **USDT Balance**     │\n"
                text += f"│ **{usdt_balance:.2f} USDT**       │\n"
                text += "└─────────────────────────┘\n\n"
                text += f"📊 **Exchange Rate:** 1 EUR = {EUR_TO_USDT_RATE} USDT\n"
                text += f"⏰ **Last Updated:** Just now\n\n"
                
                # Balance status
                if eur_balance >= 100:
                    text += "✅ **Status:** High Balance\n"
                elif eur_balance >= 10:
                    text += "🟡 **Status:** Good Balance\n"
                elif eur_balance >= 1:
                    text += "🟠 **Status:** Low Balance\n"
                else:
                    text += "🔴 **Status:** Very Low Balance\n"
                
                text += "\n💡 **Tips:**\n"
                text += "• Use crypto deposits for faster transactions\n"
                text += "• Minimum deposits start from €0.50\n"
                text += "• Your balance is stored securely"
                
                return text
            else:
                # Quick balance display
                return f"💰 **Balance:** €{eur_balance:.2f} (≈ {usdt_balance:.2f} USDT)"
            
        except Exception as e:
            logger.error(f"Error formatting balance display: {e}")
            return "❌ Error loading balance"
    
    @staticmethod
    async def get_quick_balance_notification(user_id: int) -> str:
        """Get a quick balance notification for returning users."""
        try:
            user = await user_repo.get_by_tg_id(user_id)
            if not user:
                return ""
            
            usdt_balance = user.balance
            eur_balance = BalanceService.usdt_to_eur(usdt_balance)
            
            text = f"👋 **Welcome back, {user.first_name}!**\n\n"
            text += f"💰 **Your Balance:** €{eur_balance:.2f}\n"
            text += f"🪙 **USDT Equivalent:** {usdt_balance:.2f} USDT\n\n"
            
            if eur_balance < 1:
                text += "💡 Consider adding funds to start shopping!"
            elif eur_balance < 10:
                text += "🛍️ You have enough for small purchases!"
            else:
                text += "✨ Great balance! Ready for shopping!"
            
            return text
            
        except Exception as e:
            logger.error(f"Error creating balance notification: {e}")
            return ""


# Service instance
balance_service = BalanceService()
