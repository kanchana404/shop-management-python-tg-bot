"""Crypto deposit limits and minimums configuration."""

# Realistic minimum deposit amounts for each cryptocurrency
# These are based on typical Crypto Pay minimums and practical usage
CRYPTO_MINIMUMS = {
    "USDT": 1.0,      # $1 minimum
    "USDC": 1.0,      # $1 minimum  
    "TON": 0.1,       # ~$0.50 minimum
    "BTC": 0.00001,   # ~$0.50 minimum (0.00001 BTC)
    "ETH": 0.001,     # ~$2 minimum (0.001 ETH)
    "LTC": 0.01,      # ~$0.50 minimum (0.01 LTC)
    "BNB": 0.01,      # ~$5 minimum (0.01 BNB)
    "TRX": 10.0,      # ~$1 minimum (10 TRX)
}

# Maximum deposit amounts (in USD equivalent)
CRYPTO_MAXIMUMS_USD = {
    "USDT": 10000,    # $10,000 max
    "USDC": 10000,    # $10,000 max
    "TON": 10000,     # $10,000 max
    "BTC": 10000,     # $10,000 max
    "ETH": 10000,     # $10,000 max
    "LTC": 10000,     # $10,000 max
    "BNB": 10000,     # $10,000 max
    "TRX": 10000,     # $10,000 max
}

def get_crypto_minimum(asset: str) -> float:
    """Get minimum deposit amount for a cryptocurrency."""
    return CRYPTO_MINIMUMS.get(asset.upper(), 1.0)

def get_crypto_maximum(asset: str) -> float:
    """Get maximum deposit amount for a cryptocurrency."""
    return CRYPTO_MAXIMUMS_USD.get(asset.upper(), 10000.0)

def validate_crypto_amount(amount: float, asset: str) -> tuple[bool, str]:
    """
    Validate crypto deposit amount.
    Returns (is_valid, error_message)
    """
    asset_upper = asset.upper()
    minimum = get_crypto_minimum(asset_upper)
    maximum = get_crypto_maximum(asset_upper)
    
    if amount < minimum:
        return False, f"❌ Minimum deposit amount is {minimum} {asset_upper}"
    
    if amount > maximum:
        return False, f"❌ Maximum deposit amount is {maximum} {asset_upper}"
    
    return True, ""

def format_crypto_minimum(asset: str) -> str:
    """Format minimum amount for display."""
    minimum = get_crypto_minimum(asset)
    asset_upper = asset.upper()
    
    # Format based on asset type
    if asset_upper in ["BTC"]:
        return f"{minimum:.5f} {asset_upper}"  # Show 5 decimal places for BTC
    elif asset_upper in ["ETH", "LTC", "BNB"]:
        return f"{minimum:.3f} {asset_upper}"  # Show 3 decimal places
    elif asset_upper in ["TON"]:
        return f"{minimum:.1f} {asset_upper}"  # Show 1 decimal place
    else:
        return f"{minimum:.0f} {asset_upper}"  # Show whole numbers for USDT, USDC, TRX
