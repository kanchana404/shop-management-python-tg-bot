#!/usr/bin/env python3
"""
Script to seed the database with sample data.
Run this after the bot is set up to add sample products and settings.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import db, product_repo
from app.models import ProductCreate, City, Area, CITY_AREAS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_products():
    """Seed database with sample products."""
    logger.info("Seeding products...")
    
    sample_products = [
        # Belgrade products
        ProductCreate(
            name="Premium Product A",
            description="High-quality product with excellent features. Perfect for daily use.",
            price=29.99,
            quantity=15,
            city=City.BELGRADE,
            area=Area.VRACAR,
            is_active=True
        ),
        ProductCreate(
            name="Standard Product B",
            description="Reliable and affordable product with good performance.",
            price=19.99,
            quantity=25,
            city=City.BELGRADE,
            area=Area.NOVI_BEOGRAD,
            is_active=True
        ),
        ProductCreate(
            name="Deluxe Product C",
            description="Top-tier product with premium materials and design.",
            price=49.99,
            quantity=8,
            city=City.BELGRADE,
            area=Area.STARI_GRAD,
            is_active=True
        ),
        ProductCreate(
            name="Economy Product D",
            description="Budget-friendly option without compromising on quality.",
            price=12.99,
            quantity=30,
            city=City.BELGRADE,
            area=Area.ZVEZDARA,
            is_active=True
        ),
        
        # Novi Sad products
        ProductCreate(
            name="Professional Product E",
            description="Designed for professional use with advanced features.",
            price=39.99,
            quantity=12,
            city=City.NOVI_SAD,
            area=Area.CENTAR_NS,
            is_active=True
        ),
        ProductCreate(
            name="Student Product F",
            description="Perfect for students and young professionals.",
            price=16.99,
            quantity=20,
            city=City.NOVI_SAD,
            area=Area.PODBARA,
            is_active=True
        ),
        ProductCreate(
            name="Family Product G",
            description="Great for families with multiple usage scenarios.",
            price=34.99,
            quantity=10,
            city=City.NOVI_SAD,
            area=Area.PETROVARADIN,
            is_active=True
        ),
        
        # Pančevo products
        ProductCreate(
            name="Compact Product H",
            description="Space-saving design with powerful functionality.",
            price=22.99,
            quantity=18,
            city=City.PANCEVO,
            area=Area.CENTAR_PANCEVO,
            is_active=True
        ),
        ProductCreate(
            name="Versatile Product I",
            description="Multi-purpose product suitable for various needs.",
            price=27.99,
            quantity=14,
            city=City.PANCEVO,
            area=Area.CENTAR_PANCEVO,
            is_active=True
        ),
    ]
    
    created_count = 0
    for product_data in sample_products:
        try:
            product = await product_repo.create_product(product_data)
            logger.info(f"Created product: {product.name} in {product.city}, {product.area}")
            created_count += 1
        except Exception as e:
            logger.error(f"Failed to create product {product_data.name}: {e}")
    
    logger.info(f"Successfully created {created_count} products")


async def seed_settings():
    """Seed database with default settings."""
    logger.info("Seeding settings...")
    
    default_settings = [
        {
            "key": "max_cart_items",
            "value": 50,
            "description": "Maximum items allowed in cart"
        },
        {
            "key": "max_order_amount",
            "value": 10000.0,
            "description": "Maximum order amount in EUR"
        },
        {
            "key": "min_deposit_amount", 
            "value": 10.0,
            "description": "Minimum deposit amount in EUR"
        },
        {
            "key": "max_deposit_amount",
            "value": 50000.0,
            "description": "Maximum deposit amount in EUR"
        },
        {
            "key": "deposit_timeout_hours",
            "value": 24,
            "description": "Deposit timeout in hours"
        },
        {
            "key": "order_confirmation_message",
            "value": "Thank you for your order! 📦 We will process it shortly.",
            "description": "Order confirmation message"
        },
        {
            "key": "payment_instructions",
            "value": "Please follow the payment instructions below:",
            "description": "Payment instructions text"
        }
    ]
    
    settings_count = 0
    for setting in default_settings:
        try:
            # Check if setting already exists
            existing = await db.db.settings.find_one({"key": setting["key"]})
            if not existing:
                setting["created_at"] = setting["updated_at"] = asyncio.get_event_loop().time()
                await db.db.settings.insert_one(setting)
                logger.info(f"Created setting: {setting['key']}")
                settings_count += 1
            else:
                logger.info(f"Setting already exists: {setting['key']}")
        except Exception as e:
            logger.error(f"Failed to create setting {setting['key']}: {e}")
    
    logger.info(f"Successfully created {settings_count} settings")


async def main():
    """Main function to run seeding."""
    try:
        logger.info("Starting database seeding...")
        
        # Connect to database
        await db.connect()
        
        # Seed data
        await seed_products()
        await seed_settings()
        
        logger.info("Database seeding completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        sys.exit(1)
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())










