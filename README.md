# Telegram Shop Bot

A production-ready Telegram e-commerce bot built with Pyrogram (async) and MongoDB. Features multi-bot redundancy, cryptocurrency payments, admin panel, and comprehensive order management.

## Features

### User Features
- 🛍️ **Product Browsing**: Browse products by city and area with pagination
- 🛒 **Shopping Cart**: Add items, manage quantities, checkout with balance
- 💰 **Crypto Deposits**: Support for 10+ cryptocurrencies (USDT, BTC, ETH, etc.)
- 🌐 **Multi-language**: English, Serbian, Russian support
- 📦 **Order Tracking**: View order history and status
- 💬 **Support**: Configurable support contact

### Location Support
- **Belgrade**: 15 areas (Vracar, Novi Beograd, Stari grad, etc.)
- **Novi Sad**: 4 areas (Centar, Podbara, Petrovaradin, Detelinara)
- **Pančevo**: 1 area (Centar)

### Admin Features
- 🔧 **Product Management**: CRUD operations, bulk updates, stock management
- 📋 **Order Management**: View, confirm, ship, refund orders
- 👥 **User Management**: Ban/unban, role management, balance adjustments
- 📢 **Announcements**: Broadcast messages, restock notifications
- 📊 **Analytics**: Revenue, order stats, user metrics
- ⚙️ **Settings**: Configurable text templates, support handle

### Technical Features
- 🔄 **Multi-bot Redundancy**: Multiple bot tokens for high availability
- 🚀 **Async Architecture**: High-performance async/await throughout
- 🗄️ **MongoDB**: Optimized with indexes and aggregation pipelines
- 🔒 **Rate Limiting**: Anti-spam protection
- 📅 **Scheduled Tasks**: Daily messages, cleanup jobs
- 🐳 **Docker Ready**: Complete containerization setup
- 🧪 **Tested**: Unit tests for core services
- 📝 **Logging**: Comprehensive logging and error handling

## Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd telegram-shop-bot
```

### 2. Create Environment File
```bash
cp env.example .env
```

Edit `.env` with your configuration:
```env
# Bot Tokens (comma-separated for redundancy)
BOT_TOKENS=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11,0987654321:XYZ-ABC9876def-qwe98V7U6T5R4E3W2Q1

# MongoDB
MONGO_URI=mongodb://localhost:27017/telegram_shop

# Telegram
MAIN_GROUP_ID=-1001234567890
MAIN_CHANNEL_ID=-1001234567890

# Admin
OWNER_ID=123456789
ADMIN_IDS=987654321,456789123
```

### 3. Run with Docker (Recommended)
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f telegram_bot

# Stop services  
docker-compose down
```

### 4. Manual Setup (Alternative)
```bash
# Install dependencies
pip install -r requirements.txt

# Start MongoDB
mongod --dbpath ./data/db

# Seed database
python scripts/seed_data.py

# Run bot
python -m app.bot
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKENS` | Comma-separated bot tokens | Required |
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017/telegram_shop` |
| `MAIN_GROUP_ID` | Main group for announcements | Optional |
| `MAIN_CHANNEL_ID` | Main channel for announcements | Optional |
| `OWNER_ID` | Owner Telegram ID | Required |
| `ADMIN_IDS` | Comma-separated admin IDs | Optional |
| `RATE_LIMIT_MESSAGES` | Messages per window | `5` |
| `RATE_LIMIT_WINDOW` | Rate limit window (seconds) | `60` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENVIRONMENT` | Environment (development/production) | `development` |

### Database Configuration

The bot uses MongoDB with the following collections:
- `users` - User accounts and settings
- `products` - Product catalog
- `carts` - Shopping carts
- `orders` - Order history
- `deposits` - Cryptocurrency deposits
- `announcements` - Scheduled messages
- `settings` - Bot configuration
- `audit_logs` - Admin action logs

### Multi-Bot Setup

For high availability, configure multiple bot tokens:

1. Create multiple bots with @BotFather
2. Add all tokens to `BOT_TOKENS` (comma-separated)
3. The system will automatically:
   - Start all bots simultaneously
   - Handle if some bots get banned
   - Restart failed bots automatically
   - Load balance across healthy bots

## Usage

### For Users

1. **Start**: Send `/start` to the bot
2. **Browse**: Choose "Order Products" → Select city → Select area
3. **Add to Cart**: Click "Add to Cart" on desired products
4. **Deposit**: Use "Deposit via Crypto" to add funds
5. **Checkout**: Go to "My Cart" → Click "Checkout"

### For Admins

1. **Access Panel**: Send `/admin` (requires admin role)
2. **Add Products**: Admin Panel → Products → Add Product
3. **Manage Orders**: Admin Panel → Orders → View/Update
4. **Send Announcements**: Admin Panel → Announcements → Send Broadcast
5. **View Metrics**: Admin Panel → Metrics

## API Integration

### Payment Provider Interface

The bot includes a configurable payment provider interface for cryptocurrency payments:

```python
from app.services.payment_service import PaymentProvider

class CustomPaymentProvider(PaymentProvider):
    async def create_deposit_address(self, coin: CoinType, amount_eur: float):
        # Implement your payment provider logic
        return address, amount_crypto
    
    async def check_transaction_status(self, address: str, coin: CoinType):
        # Check blockchain for confirmations
        return status, txid

# Use custom provider
from app.services.payment_service import payment_service
payment_service.provider = CustomPaymentProvider()
```

### Supported Cryptocurrencies

- **USDT**: TRC20, BEP20
- **USDC**: Solana
- **Major coins**: BTC, ETH, LTC, SOL, TRX, BNB, TON

## Development

### Project Structure
```
app/
├── config/          # Configuration management
├── models/          # Pydantic data models
├── db/              # Database repositories
├── services/        # Business logic services
├── handlers/        # Telegram message handlers
├── keyboards/       # Inline keyboard builders
├── i18n/           # Internationalization
├── utils/          # Utilities (validation, rate limiting)
├── jobs/           # Scheduled tasks
└── bot.py          # Main application

scripts/            # Database scripts
tests/             # Unit tests
```

### Adding New Features

1. **Models**: Add Pydantic models in `app/models/`
2. **Repository**: Create repository in `app/db/`
3. **Service**: Implement business logic in `app/services/`
4. **Handler**: Add handlers in `app/handlers/`
5. **Keyboard**: Create keyboards in `app/keyboards/`
6. **Tests**: Add tests in `tests/`

### Database Management

```bash
# Seed with sample data
python scripts/seed_data.py

# Export products to CSV
python scripts/export_products.py

# Import products from CSV
python scripts/import_products.py products.csv

# Database backup
mongodump --db telegram_shop --out backup/

# Database restore
mongorestore --db telegram_shop backup/telegram_shop/
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_cart_service.py

# Run integration tests
pytest tests/integration/
```

## Monitoring

### Health Checks

- **Docker**: Built-in health checks for all services
- **Bot Status**: `/health` endpoint (if web interface enabled)
- **Database**: MongoDB health monitoring

### Logs

```bash
# View bot logs
docker-compose logs -f telegram_bot

# View database logs
docker-compose logs -f mongodb

# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Metrics

The admin panel provides:
- Daily/monthly revenue
- Order statistics
- User growth
- Product performance
- Error rates

## Security

### Best Practices

1. **Environment Variables**: Never commit `.env` files
2. **Database**: Use authentication and SSL in production
3. **Rate Limiting**: Configured to prevent abuse
4. **Input Validation**: All user inputs are validated
5. **Admin Access**: Role-based access control
6. **Audit Logs**: All admin actions are logged

### Production Deployment

1. **Reverse Proxy**: Use nginx for SSL termination
2. **Firewall**: Restrict database access
3. **Monitoring**: Set up alerting for errors
4. **Backups**: Regular database backups
5. **Updates**: Use rolling deployments

## Troubleshooting

### Common Issues

**Bot not responding**
```bash
# Check bot status
docker-compose ps

# View logs
docker-compose logs telegram_bot

# Restart bot
docker-compose restart telegram_bot
```

**Database connection failed**
```bash
# Check MongoDB status
docker-compose ps mongodb

# Test connection
docker-compose exec mongodb mongosh --eval "db.runCommand('ping')"
```

**Payment not confirmed**
```bash
# Check payment provider logs
# Verify webhook configuration
# Test with smaller amounts
```

### Support

For issues and feature requests:
1. Check existing GitHub issues
2. Create detailed bug reports
3. Include logs and configuration
4. Specify environment details

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Roadmap

- [ ] Web admin dashboard
- [ ] Mobile app integration
- [ ] Advanced analytics
- [ ] Multi-currency support
- [ ] Subscription products
- [ ] Affiliate system
- [ ] AI chatbot integration



#   s h o p - m a n a g e m e n t - p y t h o n - t g - b o t 
 
 




