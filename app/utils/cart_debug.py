"""Cart debugging utilities."""

import asyncio
from app.db import db
from app.models.cart import Cart


async def check_cart_contents(user_id: int):
    """Check cart contents for a specific user."""
    try:
        collection = db.db.carts
        cart_doc = await collection.find_one({"user_id": user_id})
        
        if not cart_doc:
            print(f"❌ No cart found for user {user_id}")
            return
        
        print(f"✅ Cart found for user {user_id}")
        print(f"Cart ID: {cart_doc.get('_id')}")
        print(f"User ID: {cart_doc.get('user_id')}")
        print(f"Updated at: {cart_doc.get('updated_at')}")
        
        items = cart_doc.get('items', [])
        print(f"Items count: {len(items)}")
        
        if items:
            print("\n📦 Cart Items:")
            for i, item in enumerate(items, 1):
                print(f"  {i}. {item.get('product_name', 'Unknown')}")
                print(f"     ID: {item.get('product_id', 'Unknown')}")
                print(f"     Price: {item.get('price', 0)} EUR")
                print(f"     Quantity: {item.get('quantity', 0)}")
                print(f"     Total: {item.get('total_price', 0)} EUR")
                print()
        else:
            print("❌ No items in cart")
            
    except Exception as e:
        print(f"❌ Error checking cart: {e}")


async def list_all_carts():
    """List all carts in the database."""
    try:
        collection = db.db.carts
        carts = await collection.find().to_list(length=None)
        
        print(f"📊 Total carts in database: {len(carts)}")
        
        for cart in carts:
            user_id = cart.get('user_id')
            items_count = len(cart.get('items', []))
            print(f"User {user_id}: {items_count} items")
            
    except Exception as e:
        print(f"❌ Error listing carts: {e}")


if __name__ == "__main__":
    # Example usage
    async def main():
        await list_all_carts()
        print("\n" + "="*50 + "\n")
        # Replace with actual user ID to check specific cart
        await check_cart_contents(6616925646)  # Your user ID from the error
    
    asyncio.run(main())


