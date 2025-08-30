// MongoDB initialization script
// This script runs when the MongoDB container starts for the first time

// Switch to the application database
db = db.getSiblingDB('telegram_shop');

// Create application user
db.createUser({
  user: 'telegram_shop',
  pwd: process.env.MONGO_PASSWORD || 'shoppass123',
  roles: [
    {
      role: 'readWrite',
      db: 'telegram_shop'
    }
  ]
});

// Create collections with validation
db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['tg_id', 'created_at'],
      properties: {
        tg_id: {
          bsonType: 'long',
          description: 'Telegram user ID - required'
        },
        username: {
          bsonType: ['string', 'null'],
          description: 'Telegram username'
        },
        balance: {
          bsonType: 'double',
          minimum: 0,
          description: 'User balance in EUR'
        },
        language_code: {
          bsonType: 'string',
          enum: ['en', 'sr', 'ru'],
          description: 'User language code'
        },
        roles: {
          bsonType: 'array',
          items: {
            bsonType: 'string',
            enum: ['owner', 'admin', 'staff', 'user']
          }
        },
        is_banned: {
          bsonType: 'bool',
          description: 'Whether user is banned'
        }
      }
    }
  }
});

db.createCollection('products', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name', 'price', 'city', 'area', 'created_at'],
      properties: {
        name: {
          bsonType: 'string',
          minLength: 1,
          maxLength: 100,
          description: 'Product name - required'
        },
        price: {
          bsonType: 'double',
          minimum: 0.01,
          description: 'Product price in EUR - required'
        },
        quantity: {
          bsonType: 'int',
          minimum: 0,
          description: 'Available quantity'
        },
        city: {
          bsonType: 'string',
          enum: ['Belgrade', 'Novi Sad', 'Pančevo'],
          description: 'City - required'
        },
        area: {
          bsonType: 'string',
          description: 'Area - required'
        },
        is_active: {
          bsonType: 'bool',
          description: 'Whether product is active'
        }
      }
    }
  }
});

// Insert sample products
db.products.insertMany([
  {
    name: 'Sample Product 1',
    description: 'This is a sample product for testing purposes.',
    photos: [],
    price: 25.99,
    quantity: 10,
    city: 'Belgrade',
    area: 'Vracar',
    is_active: true,
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    name: 'Sample Product 2',
    description: 'Another sample product with different specifications.',
    photos: [],
    price: 45.50,
    quantity: 5,
    city: 'Belgrade',
    area: 'Novi Beograd',
    is_active: true,
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    name: 'Sample Product 3',
    description: 'A sample product available in Novi Sad.',
    photos: [],
    price: 15.75,
    quantity: 20,
    city: 'Novi Sad',
    area: 'Centar',
    is_active: true,
    created_at: new Date(),
    updated_at: new Date()
  }
]);

// Create other collections
db.createCollection('carts');
db.createCollection('orders');
db.createCollection('deposits');
db.createCollection('announcements');
db.createCollection('audit_logs');

// Insert default settings
db.createCollection('settings');
db.settings.insertMany([
  {
    key: 'support_handle',
    value: '@grofshop',
    description: 'Support contact handle',
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    key: 'daily_message_text',
    value: '🛍️ Check out our daily deals! Use /start to browse products.',
    description: 'Daily message text',
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    key: 'daily_message_enabled',
    value: true,
    description: 'Whether daily message is enabled',
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    key: 'welcome_message',
    value: 'Welcome to our shop! 🛍️',
    description: 'Welcome message for new users',
    created_at: new Date(),
    updated_at: new Date()
  }
]);

print('Database initialization completed successfully!');

