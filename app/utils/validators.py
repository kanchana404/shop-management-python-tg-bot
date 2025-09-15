"""Validation utilities."""

import re
from typing import Optional, Tuple
from decimal import Decimal, InvalidOperation


def validate_amount(amount_str: str) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Validate amount string and convert to float.
    
    Returns:
        tuple: (is_valid, amount, error_message)
    """
    try:
        # Remove any spaces and convert commas to dots
        amount_str = amount_str.strip().replace(',', '.')
        
        # Check if it's a valid number format
        if not re.match(r'^\d+\.?\d*$', amount_str):
            return False, None, "Invalid number format"
        
        # Convert to Decimal for precise arithmetic
        amount_decimal = Decimal(amount_str)
        amount = float(amount_decimal)
        
        # Check minimum amount
        if amount < 0.01:
            return False, None, "Amount must be at least 0.01 EUR"
        
        # Check maximum amount
        if amount > 50000:
            return False, None, "Amount cannot exceed 50,000 EUR"
        
        # Check decimal places (max 2)
        if amount_decimal.as_tuple().exponent < -2:
            return False, None, "Amount can have at most 2 decimal places"
        
        return True, amount, None
        
    except (InvalidOperation, ValueError, OverflowError):
        return False, None, "Invalid number format"


def validate_username(username: str) -> bool:
    """Validate Telegram username format."""
    if not username:
        return True  # Username is optional
    
    # Remove @ if present
    username = username.lstrip('@')
    
    # Telegram username rules:
    # - 5-32 characters
    # - Only letters, numbers, and underscores
    # - Must start with a letter
    if len(username) < 5 or len(username) > 32:
        return False
    
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        return False
    
    return True


def validate_product_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate product name."""
    if not name or not name.strip():
        return False, "Product name cannot be empty"
    
    name = name.strip()
    
    if len(name) < 2:
        return False, "Product name must be at least 2 characters"
    
    if len(name) > 100:
        return False, "Product name cannot exceed 100 characters"
    
    # Check for valid characters (allow most Unicode characters)
    if not re.match(r'^[a-zA-Z0-9\s\-_.,!?()]+$', name, re.UNICODE):
        return False, "Product name contains invalid characters"
    
    return True, None


def validate_product_description(description: str) -> Tuple[bool, Optional[str]]:
    """Validate product description."""
    if not description or not description.strip():
        return False, "Product description cannot be empty"
    
    description = description.strip()
    
    if len(description) < 10:
        return False, "Product description must be at least 10 characters"
    
    if len(description) > 1000:
        return False, "Product description cannot exceed 1000 characters"
    
    return True, None


def validate_quantity(quantity_str: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """Validate quantity string and convert to int."""
    try:
        quantity_str = quantity_str.strip()
        
        if not re.match(r'^\d+$', quantity_str):
            return False, None, "Quantity must be a positive integer"
        
        quantity = int(quantity_str)
        
        if quantity < 0:
            return False, None, "Quantity cannot be negative"
        
        if quantity > 10000:
            return False, None, "Quantity cannot exceed 10,000"
        
        return True, quantity, None
        
    except (ValueError, OverflowError):
        return False, None, "Invalid quantity format"


def validate_price(price_str: str) -> Tuple[bool, Optional[float], Optional[str]]:
    """Validate price string and convert to float."""
    try:
        # Remove any spaces and currency symbols
        price_str = price_str.strip().replace('€', '').replace('EUR', '').replace(',', '.')
        
        if not re.match(r'^\d+\.?\d*$', price_str):
            return False, None, "Invalid price format"
        
        price_decimal = Decimal(price_str)
        price = float(price_decimal)
        
        if price < 0.01:
            return False, None, "Price must be at least 0.01 EUR"
        
        if price > 100000:
            return False, None, "Price cannot exceed 100,000 EUR"
        
        # Check decimal places (max 2)
        if price_decimal.as_tuple().exponent < -2:
            return False, None, "Price can have at most 2 decimal places"
        
        return True, price, None
        
    except (InvalidOperation, ValueError, OverflowError):
        return False, None, "Invalid price format"


def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Sanitize text input by removing/escaping potentially harmful content."""
    if not text:
        return ""
    
    # Strip whitespace
    text = text.strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove or escape potentially harmful characters
    # For now, just remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    return text


def format_currency(amount: float, currency: str = "EUR") -> str:
    """Format amount as currency."""
    return f"{amount:.2f} {currency}"


def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value:.1f}%"











