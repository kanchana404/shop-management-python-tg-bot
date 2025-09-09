"""Crypto Pay service for handling cryptocurrency payments."""

import aiohttp
import hashlib
import hmac
import json
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
from app.config.settings import settings

logger = logging.getLogger(__name__)


class CryptoPayService:
    """Crypto Pay API service."""
    
    def __init__(self):
        """Initialize Crypto Pay service."""
        self.token = settings.crypto_pay_token
        self.testnet = settings.crypto_pay_testnet
        
        if self.testnet:
            self.base_url = "https://testnet-pay.crypt.bot"
        else:
            self.base_url = "https://pay.crypt.bot"
        
        if not self.token:
            logger.warning("Crypto Pay token not configured. Crypto payments will be disabled.")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Crypto-Pay-API-Token": self.token,
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request to Crypto Pay."""
        if not self.token:
            raise ValueError("Crypto Pay token not configured")
        
        url = f"{self.base_url}/api/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            if method.upper() == "GET":
                # For GET requests, add data as query parameters
                params = data if data else {}
                async with session.get(url, headers=self._get_headers(), params=params) as response:
                    result = await response.json()
            else:
                async with session.post(url, headers=self._get_headers(), json=data) as response:
                    result = await response.json()
            
            logger.info(f"Crypto Pay API response: {result}")
            
            if not result.get("ok"):
                error = result.get("error", "Unknown error")
                logger.error(f"Crypto Pay API error: {error}")
                raise Exception(f"Crypto Pay API error: {error}")
            
            return result.get("result", {})
    
    async def get_me(self) -> Dict[str, Any]:
        """Test app authentication."""
        try:
            result = await self._make_request("GET", "getMe")
            logger.info(f"Crypto Pay getMe result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in getMe: {e}")
            raise
    
    async def create_invoice(
        self,
        amount: str,
        asset: str = "USDT",
        currency_type: str = "crypto",
        description: Optional[str] = None,
        hidden_message: Optional[str] = None,
        paid_btn_name: Optional[str] = None,
        paid_btn_url: Optional[str] = None,
        payload: Optional[str] = None,
        allow_comments: bool = True,
        allow_anonymous: bool = True,
        expires_in: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new payment invoice."""
        data = {
            "amount": amount,
            "asset": asset,
            "currency_type": currency_type,
            "allow_comments": allow_comments,
            "allow_anonymous": allow_anonymous
        }
        
        if description:
            data["description"] = description
        if hidden_message:
            data["hidden_message"] = hidden_message
        if paid_btn_name:
            data["paid_btn_name"] = paid_btn_name
        if paid_btn_url:
            data["paid_btn_url"] = paid_btn_url
        if payload:
            data["payload"] = payload
        if expires_in:
            data["expires_in"] = expires_in
        
        return await self._make_request("POST", "createInvoice", data)
    
    async def create_fiat_invoice(
        self,
        amount: str,
        fiat: str = "USD",
        accepted_assets: Optional[str] = None,
        description: Optional[str] = None,
        hidden_message: Optional[str] = None,
        paid_btn_name: Optional[str] = None,
        paid_btn_url: Optional[str] = None,
        payload: Optional[str] = None,
        allow_comments: bool = True,
        allow_anonymous: bool = True,
        expires_in: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new fiat payment invoice."""
        data = {
            "amount": amount,
            "currency_type": "fiat",
            "fiat": fiat,
            "allow_comments": allow_comments,
            "allow_anonymous": allow_anonymous
        }
        
        if accepted_assets:
            data["accepted_assets"] = accepted_assets
        if description:
            data["description"] = description
        if hidden_message:
            data["hidden_message"] = hidden_message
        if paid_btn_name:
            data["paid_btn_name"] = paid_btn_name
        if paid_btn_url:
            data["paid_btn_url"] = paid_btn_url
        if payload:
            data["payload"] = payload
        if expires_in:
            data["expires_in"] = expires_in
        
        return await self._make_request("POST", "createInvoice", data)
    
    async def delete_invoice(self, invoice_id: int) -> bool:
        """Delete an invoice."""
        data = {"invoice_id": invoice_id}
        result = await self._make_request("POST", "deleteInvoice", data)
        return result is True
    
    async def get_invoices(
        self,
        asset: Optional[str] = None,
        fiat: Optional[str] = None,
        invoice_ids: Optional[str] = None,
        status: Optional[str] = None,
        offset: int = 0,
        count: int = 100
    ) -> List[Dict[str, Any]]:
        """Get invoices created by the app."""
        data = {"offset": offset, "count": count}
        
        if asset:
            data["asset"] = asset
        if fiat:
            data["fiat"] = fiat
        if invoice_ids:
            data["invoice_ids"] = invoice_ids
        if status:
            data["status"] = status
        
        return await self._make_request("GET", "getInvoices", data)
    
    async def get_balance(self) -> List[Dict[str, Any]]:
        """Get app balance."""
        return await self._make_request("GET", "getBalance")
    
    async def get_exchange_rates(self) -> List[Dict[str, Any]]:
        """Get exchange rates."""
        return await self._make_request("GET", "getExchangeRates")
    
    async def get_usd_rate(self, asset: str) -> Optional[float]:
        """Get USD rate for a specific asset."""
        try:
            rates = await self.get_exchange_rates()
            for rate in rates:
                if (rate.get('source') == asset and 
                    rate.get('target') == 'USD' and 
                    rate.get('is_valid', False)):
                    return float(rate.get('rate', 0))
            return None
        except Exception as e:
            logger.error(f"Error getting USD rate for {asset}: {e}")
            return None
    
    async def convert_to_usd(self, amount: str, asset: str) -> Optional[float]:
        """Convert crypto amount to USD using current exchange rates."""
        try:
            rate = await self.get_usd_rate(asset)
            if rate:
                return float(amount) * rate
            return None
        except Exception as e:
            logger.error(f"Error converting {amount} {asset} to USD: {e}")
            return None
    
    async def get_currencies(self) -> Dict[str, List[str]]:
        """Get supported currencies."""
        return await self._make_request("GET", "getCurrencies")
    
    async def transfer(
        self,
        user_id: int,
        asset: str,
        amount: str,
        spend_id: str,
        comment: Optional[str] = None,
        disable_send_notification: bool = False
    ) -> Dict[str, Any]:
        """Transfer coins to a user."""
        data = {
            "user_id": user_id,
            "asset": asset,
            "amount": amount,
            "spend_id": spend_id,
            "disable_send_notification": disable_send_notification
        }
        
        if comment:
            data["comment"] = comment
        
        return await self._make_request("POST", "transfer", data)
    
    async def get_transfers(
        self,
        asset: Optional[str] = None,
        transfer_ids: Optional[str] = None,
        spend_id: Optional[str] = None,
        offset: int = 0,
        count: int = 100
    ) -> List[Dict[str, Any]]:
        """Get transfers created by the app."""
        data = {"offset": offset, "count": count}
        
        if asset:
            data["asset"] = asset
        if transfer_ids:
            data["transfer_ids"] = transfer_ids
        if spend_id:
            data["spend_id"] = spend_id
        
        return await self._make_request("GET", "getTransfers", data)
    
    async def get_stats(
        self,
        start_at: Optional[str] = None,
        end_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get app statistics."""
        data = {}
        
        if start_at:
            data["start_at"] = start_at
        if end_at:
            data["end_at"] = end_at
        
        return await self._make_request("GET", "getStats", data)
    
    def verify_webhook_signature(self, token: str, body: str, signature: str) -> bool:
        """Verify webhook signature."""
        if not self.token:
            return False
        
        # Create secret from token
        secret = hashlib.sha256(self.token.encode()).digest()
        
        # Create HMAC signature
        hmac_obj = hmac.new(secret, body.encode(), hashlib.sha256)
        expected_signature = hmac_obj.hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    async def create_deposit_invoice(
        self,
        user_id: int,
        amount: str,
        asset: str = "USDT",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a deposit invoice for a user and store in database."""
        if not description:
            description = f"Deposit {amount} {asset} to your account"
        
        payload = json.dumps({
            "user_id": user_id,
            "type": "deposit",
            "amount": amount,
            "asset": asset
        })
        
        # Create invoice via API
        api_response = await self.create_invoice(
            amount=amount,
            asset=asset,
            description=description,
            payload=payload,
            paid_btn_name="callback",
            paid_btn_url="https://t.me/your_bot_username",  # Replace with your bot username
            expires_in=3600  # 1 hour
        )
        
        # Store invoice in database
        if api_response and api_response.get('invoice_id'):
            try:
                from app.db.invoice_repository import invoice_repo
                from app.models.invoice import InvoiceCreate, InvoiceType
                from datetime import datetime, timedelta
                
                invoice_data = InvoiceCreate(
                    invoice_id=api_response['invoice_id'],
                    user_id=user_id,
                    type=InvoiceType.DEPOSIT,
                    amount=amount,
                    asset=asset,
                    currency_type="crypto",
                    bot_invoice_url=api_response.get('bot_invoice_url'),
                    mini_app_invoice_url=api_response.get('mini_app_invoice_url'),
                    description=description,
                    payload_data={
                        "user_id": user_id,
                        "type": "deposit",
                        "amount": amount,
                        "asset": asset
                    },
                    expires_at=datetime.utcnow() + timedelta(hours=1)
                )
                
                stored_invoice = await invoice_repo.create_invoice(invoice_data)
                if stored_invoice:
                    logger.info(f"Invoice {api_response['invoice_id']} stored in database for user {user_id}")
                else:
                    logger.error(f"Failed to store invoice {api_response['invoice_id']} in database")
                    
            except Exception as e:
                logger.error(f"Error storing invoice in database: {e}")
        
        return api_response
    
    async def create_order_invoice(
        self,
        user_id: int,
        order_id: str,
        amount: str,
        asset: str = "USDT",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an invoice for an order and store in database."""
        if not description:
            description = f"Payment for order #{order_id}"
        
        payload = json.dumps({
            "user_id": user_id,
            "type": "order",
            "order_id": order_id,
            "amount": amount,
            "asset": asset
        })
        
        # Create invoice via API
        api_response = await self.create_invoice(
            amount=amount,
            asset=asset,
            description=description,
            payload=payload,
            paid_btn_name="callback",
            paid_btn_url="https://t.me/your_bot_username",  # Replace with your bot username
            expires_in=1800  # 30 minutes
        )
        
        # Store invoice in database
        if api_response and api_response.get('invoice_id'):
            try:
                from app.db.invoice_repository import invoice_repo
                from app.models.invoice import InvoiceCreate, InvoiceType
                from datetime import datetime, timedelta
                
                invoice_data = InvoiceCreate(
                    invoice_id=api_response['invoice_id'],
                    user_id=user_id,
                    type=InvoiceType.ORDER,
                    amount=amount,
                    asset=asset,
                    currency_type="crypto",
                    bot_invoice_url=api_response.get('bot_invoice_url'),
                    mini_app_invoice_url=api_response.get('mini_app_invoice_url'),
                    description=description,
                    order_id=order_id,
                    payload_data={
                        "user_id": user_id,
                        "type": "order",
                        "order_id": order_id,
                        "amount": amount,
                        "asset": asset
                    },
                    expires_at=datetime.utcnow() + timedelta(minutes=30)
                )
                
                stored_invoice = await invoice_repo.create_invoice(invoice_data)
                if stored_invoice:
                    logger.info(f"Order invoice {api_response['invoice_id']} stored in database for user {user_id}")
                else:
                    logger.error(f"Failed to store order invoice {api_response['invoice_id']} in database")
                    
            except Exception as e:
                logger.error(f"Error storing order invoice in database: {e}")
        
        return api_response


# Service instance
crypto_pay_service = CryptoPayService()
