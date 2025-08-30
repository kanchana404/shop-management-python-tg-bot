"""Deposit model and schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class CoinType(str, Enum):
    """Supported cryptocurrencies."""
    USDT_TRC20 = "USDT_TRC20"
    USDT_BEP20 = "USDT_BEP20"
    USDC_SOL = "USDC_SOL"
    TON = "TON"
    BTC = "BTC"
    LTC = "LTC"
    ETH = "ETH"
    SOL = "SOL"
    TRX = "TRX"
    BNB = "BNB"


class DepositStatus(str, Enum):
    """Deposit status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    EXPIRED = "expired"


class NetworkType(str, Enum):
    """Blockchain networks."""
    TRC20 = "TRC20"
    BEP20 = "BEP20"
    SOLANA = "SOL"
    BITCOIN = "BTC"
    ETHEREUM = "ETH"
    LITECOIN = "LTC"
    TRON = "TRX"
    TON = "TON"


# Mapping coins to their networks
COIN_NETWORKS = {
    CoinType.USDT_TRC20: NetworkType.TRC20,
    CoinType.USDT_BEP20: NetworkType.BEP20,
    CoinType.USDC_SOL: NetworkType.SOLANA,
    CoinType.TON: NetworkType.TON,
    CoinType.BTC: NetworkType.BITCOIN,
    CoinType.LTC: NetworkType.LITECOIN,
    CoinType.ETH: NetworkType.ETHEREUM,
    CoinType.SOL: NetworkType.SOLANA,
    CoinType.TRX: NetworkType.TRON,
    CoinType.BNB: NetworkType.BEP20,
}


class Deposit(BaseModel):
    """Deposit model."""
    id: Optional[str] = Field(None, alias="_id")
    user_id: int = Field(..., description="User's Telegram ID")
    amount_eur: float = Field(..., description="Deposit amount in EUR")
    amount_crypto: Optional[float] = Field(None, description="Deposit amount in cryptocurrency")
    coin: CoinType = Field(..., description="Cryptocurrency type")
    network: NetworkType = Field(..., description="Blockchain network")
    address: Optional[str] = Field(None, description="Deposit address")
    txid: Optional[str] = Field(None, description="Transaction ID")
    status: DepositStatus = Field(default=DepositStatus.PENDING, description="Deposit status")
    expires_at: Optional[datetime] = Field(None, description="Deposit expiration time")
    confirmed_at: Optional[datetime] = Field(None, description="Confirmation time")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic config."""
        populate_by_name = True
        use_enum_values = True


class DepositCreate(BaseModel):
    """Schema for creating a deposit."""
    user_id: int
    amount_eur: float
    coin: CoinType
    
    @property
    def network(self) -> NetworkType:
        """Get network for the selected coin."""
        return COIN_NETWORKS[self.coin]


class DepositUpdate(BaseModel):
    """Schema for updating a deposit."""
    amount_crypto: Optional[float] = None
    address: Optional[str] = None
    txid: Optional[str] = None
    status: Optional[DepositStatus] = None
    confirmed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
