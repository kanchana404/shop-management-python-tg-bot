# 🔗 Crypto Pay Webhook Connection Guide

## 🎯 **Current Setup Status**
✅ Webhook server implemented (`app/webhooks/crypto_pay_webhook.py`)  
✅ Signature verification implemented  
✅ Payment processing handlers ready  
✅ State management system working  

## 🚀 **Quick Setup (5 Steps)**

### **Step 1: Configure Environment**
Update your `.env` file:
```env
# Crypto Pay Configuration
CRYPTO_PAY_TOKEN=123456789:AAzQcZWQqQAbsfgPnOLr4FHC8Doa4L7KryC
CRYPTO_PAY_TESTNET=true
```

### **Step 2: Start Webhook Server**
```bash
# Terminal 1: Start webhook server
python start_webhook.py
```
You should see:
```
🚀 Starting Crypto Pay Webhook Server...
📊 Environment: development
🔗 Webhook URL: http://localhost:8000/webhook/crypto-pay
💚 Health Check: http://localhost:8000/health
```

### **Step 3: Make Webhook Publicly Accessible**

#### **Option A: Using ngrok (Recommended for testing)**
```bash
# Terminal 2: Start ngrok
ngrok http 8000
```
You'll get a public URL like: `https://abc123.ngrok.io`

#### **Option B: Using Cloudflare Tunnel (Alternative)**
```bash
# Install cloudflared
cloudflared tunnel --url http://localhost:8000
```

### **Step 4: Configure Webhook in Crypto Pay**

1. **Open Telegram** and go to `@CryptoBot` (or `@CryptoTestnetBot` for testnet)
2. **Navigate:** Crypto Pay → My Apps → [Your App] → Settings
3. **Click:** Webhooks... → 🌕 Enable Webhooks
4. **Enter URL:** `https://your-ngrok-url.ngrok.io/webhook/crypto-pay`
5. **Select Events:** ✅ invoice_paid
6. **Save configuration**

### **Step 5: Test the Connection**

Create a test payment:
1. Use your bot to create a crypto deposit
2. Select USDT, enter amount (e.g., "1")
3. Complete the payment in Crypto Pay
4. Check webhook logs for processing

## 🔧 **Webhook URL Examples**

### **Development (ngrok):**
```
https://abc123.ngrok.io/webhook/crypto-pay
```

### **Production (your domain):**
```
https://yourdomain.com/webhook/crypto-pay
```

### **Local testing:**
```
http://localhost:8000/webhook/crypto-pay
```

## 📊 **Webhook Security**

Your implementation includes:
- ✅ **Signature Verification** using HMAC-SHA256
- ✅ **Token-based Security** 
- ✅ **Request Body Validation**
- ✅ **Error Handling**

### **Signature Verification Process:**
```python
# Your implementation automatically:
1. Gets signature from headers: crypto-pay-api-signature
2. Creates secret: SHA256(your_token)
3. Signs request body: HMAC-SHA256(secret, body)
4. Compares signatures for security
```

## 🎯 **What Happens When Payment Succeeds**

### **Webhook Flow:**
```
1. User completes payment in Crypto Pay
2. Crypto Pay sends POST to your webhook URL
3. Your server verifies signature
4. Processes payment (updates balance/order)
5. Sends confirmation to user
6. Returns success response to Crypto Pay
```

### **Webhook Data Structure:**
```json
{
  "update_id": 12345,
  "update_type": "invoice_paid",
  "request_date": "2025-01-20T10:30:00Z",
  "payload": {
    "invoice_id": 67890,
    "status": "paid",
    "amount": "5.0",
    "asset": "USDT",
    "payload": "deposit:6616925646:5.0:USDT",
    "paid_at": "2025-01-20T10:30:00Z"
  }
}
```

## 🧪 **Testing Your Setup**

### **1. Health Check:**
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

### **2. Webhook Test (Manual):**
```bash
curl -X POST http://localhost:8000/webhook/crypto-pay \
  -H "Content-Type: application/json" \
  -H "crypto-pay-api-signature: test_signature" \
  -d '{
    "update_id": 1,
    "update_type": "invoice_paid",
    "request_date": "2025-01-20T10:30:00Z",
    "payload": {
      "invoice_id": 123456,
      "status": "paid",
      "amount": "5.0",
      "asset": "USDT",
      "payload": "deposit:6616925646:5.0:USDT"
    }
  }'
```

### **3. Real Payment Test:**
1. Start bot: `python main.py`
2. Start webhook: `python start_webhook.py` 
3. Start ngrok: `ngrok http 8000`
4. Configure webhook in @CryptoBot
5. Create test deposit via bot
6. Complete payment
7. Verify logs show processing

## 🛠️ **Troubleshooting**

### **Common Issues:**

**🔴 Webhook not receiving calls:**
- Check ngrok is running and URL is correct
- Verify webhook URL in Crypto Pay settings
- Test health endpoint: `curl http://your-ngrok-url/health`

**🔴 Signature verification fails:**
- Ensure CRYPTO_PAY_TOKEN is correct in .env
- Check signature header format
- For testing, use "test_signature" header

**🔴 Database not updating:**
- Check webhook processing logs
- Verify user exists in database
- Check invoice payload format

### **Debug Commands:**
```bash
# Check webhook server
curl http://localhost:8000/health

# Check ngrok status
curl http://localhost:4040/api/tunnels

# View logs in real-time
tail -f bot.log
```

## 📱 **Mobile Testing**

1. **Create test deposit** on mobile
2. **Pay with Crypto Pay** mobile app
3. **Check webhook logs** on your computer
4. **Verify balance update** in bot

## 🚀 **Production Deployment**

### **Option 1: VPS/Server**
```bash
# Deploy to server with public IP
# Configure SSL certificate
# Use domain: https://yourdomain.com/webhook/crypto-pay
```

### **Option 2: Cloud Platforms**
- **Heroku**: Set webhook URL to your Heroku app
- **DigitalOcean**: Deploy with public IP
- **AWS/GCP**: Use load balancer with SSL

## 📊 **Monitoring Success**

✅ **Webhook receives POST requests**  
✅ **Signature verification passes**  
✅ **Database updates successfully**  
✅ **User receives confirmation message**  
✅ **No errors in logs**  

## 🎉 **You're Ready!**

Once configured:
1. Users can deposit crypto and get instant balance updates
2. Order payments are automatically processed
3. All transactions are logged and verified
4. Real-time payment notifications work

---

**💡 Need help?** Check the logs, test endpoints, and verify each step above.
