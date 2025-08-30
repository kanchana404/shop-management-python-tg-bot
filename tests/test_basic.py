"""Basic tests to verify the application setup."""

import pytest
import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.models import UserCreate, ProductCreate, City, Area


def test_settings_load():
    """Test that settings load correctly."""
    assert isinstance(settings.bot_tokens, list)
    assert settings.api_id == 6  # Default value
    assert settings.api_hash is not None
    assert settings.database_name == "telegram_shop"


def test_user_model():
    """Test user model creation."""
    user_data = UserCreate(
        tg_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User"
    )
    
    assert user_data.tg_id == 123456789
    assert user_data.username == "testuser"
    assert user_data.first_name == "Test"
    assert user_data.last_name == "User"


def test_product_model():
    """Test product model creation."""
    product_data = ProductCreate(
        name="Test Product",
        description="A test product for testing purposes",
        price=29.99,
        quantity=10,
        city=City.BELGRADE,
        area=Area.VRACAR,
        is_active=True
    )
    
    assert product_data.name == "Test Product"
    assert product_data.price == 29.99
    assert product_data.quantity == 10
    assert product_data.city == City.BELGRADE
    assert product_data.area == Area.VRACAR


def test_keyboard_imports():
    """Test that keyboard modules can be imported."""
    from app.keyboards import get_main_menu_keyboard, get_city_selection_keyboard
    
    # Test keyboard functions exist
    assert callable(get_main_menu_keyboard)
    assert callable(get_city_selection_keyboard)


def test_city_areas_mapping():
    """Test that city areas mapping is correct."""
    from app.models import CITY_AREAS
    
    # Check Belgrade has correct areas
    belgrade_areas = CITY_AREAS[City.BELGRADE]
    assert Area.VRACAR in belgrade_areas
    assert Area.NOVI_BEOGRAD in belgrade_areas
    assert len(belgrade_areas) == 15
    
    # Check Novi Sad has correct areas
    novi_sad_areas = CITY_AREAS[City.NOVI_SAD]
    assert Area.CENTAR_NS in novi_sad_areas
    assert len(novi_sad_areas) == 4
    
    # Check Pančevo has correct areas
    pancevo_areas = CITY_AREAS[City.PANCEVO]
    assert Area.CENTAR_PANCEVO in pancevo_areas
    assert len(pancevo_areas) == 1


def test_translation_system():
    """Test translation system works."""
    from app.i18n import translator, _
    
    # Test basic translation
    text = _("start.welcome", "en")
    assert isinstance(text, str)
    assert len(text) > 0
    
    # Test translation with variables
    text_with_vars = _("support.message", "en", handle="@testshop")
    assert "@testshop" in text_with_vars


if __name__ == "__main__":
    pytest.main([__file__])
