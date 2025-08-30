# Crypto Pay Integration Setup Guide

This guide will help you set up cryptocurrency payments using @CryptoBot's Crypto Pay API in your Telegram shop bot.

## 🚀 Quick Start

### 1. Create Crypto Pay App

1. **Open @CryptoBot** (or @CryptoTestnetBot for testing)
2. Go to **Crypto Pay**
3. Tap **Create App**
4. Get your **API Token**

### 2. Configure Environment

Add these variables to your `.env` file:

```env
# Crypto Pay Configuration
CRYPTO_PAY_TOKEN=your_crypto_pay_token_here
CRYPTO_PAY_TESTNET=false  # Set to true for testing
```

### 3. Test the Integration

Run the bot and test the crypto payment flow:

```bash
python -m app.bot
```

## 📋 Supported Cryptocurrencies

Your bot now supports these cryptocurrencies:

- **USDT** (Tether)
- **TON** (Toncoin)
- **BTC** (Bitcoin)
- **ETH** (Ethereum)
- **LTC** (Litecoin)
- **BNB** (Binance Coin)
- **TRX** (TRON)
- **USDC** (USD Coin)

## 💳 Payment Features

### 1. Crypto Deposits
- Users can deposit crypto to their account balance
- Automatic conversion to EUR (configurable)
- Real-time balance updates

### 2. Order Payments
- Pay for orders with cryptocurrency
- Multiple payment options (balance + crypto)
- Automatic order status updates

### 3. Exchange Rates
- Real-time crypto exchange rates
- USD-based rate display
- Rate validation

### 4. Balance Management
- View app crypto balances
- Track available vs on-hold amounts
- Multi-currency support

## 🔧 Configuration Options

### Testnet vs Mainnet

```env
# For testing (use @CryptoTestnetBot)
CRYPTO_PAY_TESTNET=true

# For production (use @CryptoBot)
CRYPTO_PAY_TESTNET=false
```

### Webhook Setup (Optional)

For real-time payment notifications:

1. **Deploy webhook server:**
```bash
python -m app.webhooks.crypto_pay_webhook
```

2. **Configure webhook URL in @CryptoBot:**
   - Go to your app settings
   - Enable webhooks
   - Set URL: `https://your-domain.com/webhook/crypto-pay`

## 🎯 User Flow

### Crypto Deposit Flow:
1. User clicks "💳 Crypto Deposit"
2. Selects cryptocurrency (USDT, BTC, etc.)
3. Enters amount
4. Receives payment invoice
5. Pays via @CryptoBot
6. Balance automatically updated

### Order Payment Flow:
1. User adds items to cart
2. Proceeds to checkout
3. Sees payment options (balance + crypto)
4. Selects "Pay with Crypto"
5. Receives payment invoice
6. Pays via @CryptoBot
7. Order automatically marked as paid

## 🔒 Security Features

### Webhook Verification
- HMAC-SHA256 signature verification
- Token-based authentication
- Request validation

### Payment Validation
- Amount limits (1-10,000 USDT)
- User authentication
- Order ownership verification

## 📊 Admin Features

### Balance Monitoring
- View app crypto balances
- Track payment statistics
- Monitor exchange rates

### Payment Analytics
- Payment success rates
- Popular cryptocurrencies
- Revenue tracking

## 🛠️ API Methods Available

### Core Methods:
- `create_invoice()` - Create payment invoices
- `create_fiat_invoice()` - Create fiat-based invoices
- `get_balance()` - Get app balances
- `get_exchange_rates()` - Get current rates
- `transfer()` - Send crypto to users
- `get_invoices()` - List invoices
- `get_stats()` - Get app statistics

### Webhook Handling:
- `handle_crypto_webhook()` - Process webhook updates
- `handle_crypto_deposit()` - Handle deposits
- `handle_crypto_order_payment()` - Handle order payments

## 🚨 Error Handling

### Common Issues:

1. **Token not configured:**
   ```
   WARNING: Crypto Pay token not configured. Crypto payments will be disabled.
   ```

2. **Invalid signature:**
   ```
   ERROR: Invalid webhook signature
   ```

3. **API errors:**
   ```
   ERROR: Crypto Pay API error: [error_code]
   ```

### Troubleshooting:

1. **Check token format:** Should be `app_id:token`
2. **Verify testnet setting:** Match with bot (@CryptoBot vs @CryptoTestnetBot)
3. **Test API connection:** Use `get_me()` method
4. **Check webhook URL:** Must be HTTPS and publicly accessible

## 📈 Monitoring

### Logs to Watch:
```
INFO - Crypto deposit processed: User 123456, Amount 10.5 USDT
INFO - Crypto order payment processed: Order ABC123, Amount 25.0 USDT
INFO - Crypto Pay webhook processed: invoice_paid - Invoice 789
```

### Key Metrics:
- Payment success rate
- Average payment amount
- Popular cryptocurrencies
- Webhook delivery success

## 🔄 Updates and Maintenance

### Regular Tasks:
1. Monitor exchange rates
2. Check app balances
3. Review payment logs
4. Update rate limits if needed

### Security Updates:
1. Rotate API tokens periodically
2. Monitor webhook security
3. Review payment limits
4. Update signature verification

## 📞 Support

For Crypto Pay API issues:
- @CryptoBot support
- Crypto Pay documentation
- API status page

For bot integration issues:
- Check logs for errors
- Verify configuration
- Test with small amounts first

## 🎉 Success!

Your Telegram shop bot now supports cryptocurrency payments! Users can:

✅ Deposit crypto to their account
✅ Pay for orders with cryptocurrency
✅ View real-time exchange rates
✅ Track their payment history
✅ Enjoy secure, instant payments

The integration is production-ready and includes comprehensive error handling, security features, and monitoring capabilities.


