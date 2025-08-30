"""Payment service with crypto provider interface."""

from typing import Optional, Protocol
from datetime import datetime, timedelta
from app.models import Deposit, DepositCreate, DepositUpdate, DepositStatus, CoinType
# db will be imported later to avoid circular imports
from app.db.user_repository import user_repo
import logging
import secrets
import qrcode
from io import BytesIO
import base64

logger = logging.getLogger(__name__)


class PaymentProvider(Protocol):
    """Payment provider interface."""
    
    async def create_deposit_address(self, coin: CoinType, amount_eur: float) -> tuple[str, float]:
        """
        Create a deposit address for the given coin and amount.
        
        Returns:
            tuple: (address, amount_in_crypto)
        """
        ...
    
    async def check_transaction_status(self, address: str, coin: CoinType) -> tuple[DepositStatus, Optional[str]]:
        """
        Check transaction status for an address.
        
        Returns:
            tuple: (status, txid)
        """
        ...


class MockPaymentProvider:
    """Mock payment provider for development."""
    
    async def create_deposit_address(self, coin: CoinType, amount_eur: float) -> tuple[str, float]:
        """Create a mock deposit address."""
        # Generate mock address
        address_prefix = {
            CoinType.BTC: "bc1",
            CoinType.ETH: "0x",
            CoinType.USDT_TRC20: "T",
            CoinType.USDT_BEP20: "0x",
            CoinType.USDC_SOL: "",
            CoinType.TON: "UQ",
            CoinType.LTC: "ltc1",
            CoinType.SOL: "",
            CoinType.TRX: "T",
            CoinType.BNB: "bnb"
        }
        
        prefix = address_prefix.get(coin, "")
        mock_address = f"{prefix}{secrets.token_hex(20)}"
        
        # Mock exchange rates (EUR to crypto)
        mock_rates = {
            CoinType.BTC: 0.000025,  # 1 EUR = 0.000025 BTC
            CoinType.ETH: 0.0004,    # 1 EUR = 0.0004 ETH
            CoinType.USDT_TRC20: 1.1,
            CoinType.USDT_BEP20: 1.1,
            CoinType.USDC_SOL: 1.1,
            CoinType.TON: 0.5,
            CoinType.LTC: 0.015,
            CoinType.SOL: 0.008,
            CoinType.TRX: 12.0,
            CoinType.BNB: 0.002
        }
        
        rate = mock_rates.get(coin, 1.0)
        amount_crypto = round(amount_eur * rate, 8)
        
        return mock_address, amount_crypto
    
    async def check_transaction_status(self, address: str, coin: CoinType) -> tuple[DepositStatus, Optional[str]]:
        """Mock transaction status check."""
        # For development, randomly return pending or confirmed
        import random
        if random.random() < 0.1:  # 10% chance of confirmation
            return DepositStatus.CONFIRMED, f"mock_tx_{secrets.token_hex(16)}"
        return DepositStatus.PENDING, None


class PaymentService:
    """Service for managing payments and deposits."""
    
    def __init__(self, provider: PaymentProvider = None):
        self.collection = None
        self.provider = provider or MockPaymentProvider()
    
    def _get_collection(self):
        """Lazy load the database collection."""
        if self.collection is None:
            from app.db import db
            self.collection = db.db.deposits
        return self.collection
    
    async def create_deposit(self, user_id: int, amount_eur: float, coin: CoinType) -> Optional[Deposit]:
        """Create a new deposit."""
        try:
            # Create deposit address
            address, amount_crypto = await self.provider.create_deposit_address(coin, amount_eur)
            
            # Create deposit record
            deposit_data = DepositCreate(
                user_id=user_id,
                amount_eur=amount_eur,
                coin=coin
            )
            
            deposit_dict = deposit_data.dict(exclude_unset=True, by_alias=True)
            deposit_dict.update({
                "amount_crypto": amount_crypto,
                "address": address,
                "network": deposit_data.network.value,
                "expires_at": datetime.utcnow() + timedelta(hours=24),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
            collection = self._get_collection()
            result = await collection.insert_one(deposit_dict)
            
            # Get created deposit
            deposit_doc = await collection.find_one({"_id": result.inserted_id})
            return Deposit(**deposit_doc)
            
        except Exception as e:
            logger.error(f"Error creating deposit: {e}")
            return None
    
    async def get_deposit_by_id(self, deposit_id: str) -> Optional[Deposit]:
        """Get deposit by ID."""
        try:
            from bson import ObjectId
            collection = self._get_collection()
            deposit_doc = await collection.find_one({"_id": ObjectId(deposit_id)})
            return Deposit(**deposit_doc) if deposit_doc else None
        except Exception as e:
            logger.error(f"Error getting deposit: {e}")
            return None
    
    async def check_deposit_status(self, deposit_id: str) -> Optional[Deposit]:
        """Check and update deposit status."""
        try:
            deposit = await self.get_deposit_by_id(deposit_id)
            if not deposit or deposit.status != DepositStatus.PENDING:
                return deposit
            
            # Check if expired
            if deposit.expires_at and datetime.utcnow() > deposit.expires_at:
                await self.update_deposit_status(deposit_id, DepositStatus.EXPIRED)
                return await self.get_deposit_by_id(deposit_id)
            
            # Check with provider
            status, txid = await self.provider.check_transaction_status(deposit.address, deposit.coin)
            
            if status == DepositStatus.CONFIRMED:
                # Update deposit and user balance
                await self.confirm_deposit(deposit_id, txid)
            
            return await self.get_deposit_by_id(deposit_id)
            
        except Exception as e:
            logger.error(f"Error checking deposit status: {e}")
            return None
    
    async def confirm_deposit(self, deposit_id: str, txid: str = None) -> bool:
        """Confirm a deposit and credit user balance."""
        try:
            deposit = await self.get_deposit_by_id(deposit_id)
            if not deposit or deposit.status != DepositStatus.PENDING:
                return False
            
            # Update deposit status
            update_data = DepositUpdate(
                status=DepositStatus.CONFIRMED,
                txid=txid,
                confirmed_at=datetime.utcnow()
            )
            
            from bson import ObjectId
            collection = self._get_collection()
            await collection.update_one(
                {"_id": ObjectId(deposit_id)},
                {"$set": update_data.dict(exclude_unset=True)}
            )
            
            # Credit user balance
            await user_repo.update_balance(deposit.user_id, deposit.amount_eur)
            
            return True
            
        except Exception as e:
            logger.error(f"Error confirming deposit: {e}")
            return False
    
    async def update_deposit_status(self, deposit_id: str, status: DepositStatus) -> bool:
        """Update deposit status."""
        try:
            from bson import ObjectId
            
            update_data = DepositUpdate(status=status)
            collection = self._get_collection()
            result = await collection.update_one(
                {"_id": ObjectId(deposit_id)},
                {"$set": update_data.dict(exclude_unset=True)}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating deposit status: {e}")
            return False
    
    async def get_user_deposits(self, user_id: int, limit: int = 20) -> list[Deposit]:
        """Get user's deposits."""
        try:
            collection = self._get_collection()
            cursor = collection.find({"user_id": user_id})
            cursor = cursor.sort("created_at", -1).limit(limit)
            
            deposits = []
            async for deposit_doc in cursor:
                deposits.append(Deposit(**deposit_doc))
            
            return deposits
            
        except Exception as e:
            logger.error(f"Error getting user deposits: {e}")
            return []
    
    def generate_qr_code(self, address: str) -> str:
        """Generate QR code for address."""
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(address)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return ""
    
    async def cleanup_expired_deposits(self):
        """Clean up expired deposits."""
        try:
            now = datetime.utcnow()
            collection = self._get_collection()
            result = await collection.update_many(
                {
                    "status": DepositStatus.PENDING.value,
                    "expires_at": {"$lt": now}
                },
                {"$set": {
                    "status": DepositStatus.EXPIRED.value,
                    "updated_at": now
                }}
            )
            
            logger.info(f"Marked {result.modified_count} deposits as expired")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired deposits: {e}")


# Service instance
payment_service = PaymentService()
