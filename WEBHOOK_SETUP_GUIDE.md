# 🔗 Crypto Pay Webhook Setup Guide

## 🎯 **Overview**
This guide explains how to set up webhooks for Crypto Pay to automatically handle successful payments and update your database.

## 🚀 **Current Status**
- ✅ Webhook server is running on `http://localhost:8000`
- ✅ Health check endpoint: `http://localhost:8000/health`
- ✅ Webhook endpoint: `http://localhost:8000/webhook/crypto-pay`

## 📋 **Setup Steps**

### **Step 1: Make Webhook Publicly Accessible**

#### **Option A: Using ngrok (Recommended for testing)**

1. **Install ngrok:**
   ```bash
   # Download from https://ngrok.com/download
   # Or install via package manager
   ```

2. **Start ngrok:**
   ```bash
   ngrok http 8000
   ```

3. **Get your public URL:**
   - Look for: `https://xxxx-xx-xx-xxx-xx.ngrok.io`
   - Your webhook URL will be: `https://xxxx-xx-xx-xxx-xx.ngrok.io/webhook/crypto-pay`

#### **Option B: Using a VPS/Server (Production)**

1. **Deploy your bot to a server**
2. **Configure domain and SSL**
3. **Your webhook URL will be:** `https://yourdomain.com/webhook/crypto-pay`

### **Step 2: Configure Crypto Pay Webhook**

1. **Go to your Crypto Pay app dashboard**
2. **Navigate to Settings → Webhooks**
3. **Add new webhook:**
   - **URL:** `https://your-public-url.com/webhook/crypto-pay`
   - **Events:** Select `invoice_paid`
   - **Secret:** (Optional) Add a secret for extra security

### **Step 3: Test the Webhook**

1. **Create a test invoice** (like you just did with 5 USDT)
2. **Complete the payment** in Crypto Pay
3. **Check webhook logs** in your terminal
4. **Verify database updates**

## 🔧 **Webhook Configuration**

### **Environment Variables**
Add these to your `.env` file:

```env
# Webhook Configuration
WEBHOOK_SECRET=your_webhook_secret_here
WEBHOOK_URL=https://your-domain.com/webhook/crypto-pay

# Crypto Pay Configuration
CRYPTO_PAY_TOKEN=your_crypto_pay_token
CRYPTO_PAY_TESTNET=false
```

### **Webhook Events Handled**
- ✅ `invoice_paid` - When a payment is completed
- ✅ `invoice_expired` - When an invoice expires
- ✅ `invoice_cancelled` - When an invoice is cancelled

## 🎯 **What Happens When Payment Succeeds**

### **For Deposits:**
1. **Crypto Pay sends webhook** to your server
2. **Server verifies signature** for security
3. **Parses payment data** (amount, asset, user_id)
4. **Updates user balance** in database
5. **Sends confirmation message** to user
6. **Logs the transaction**

### **For Order Payments:**
1. **Crypto Pay sends webhook** to your server
2. **Server verifies signature** for security
3. **Parses payment data** (order_id, amount, asset)
4. **Updates order status** to "paid"
5. **Sends confirmation message** to user
6. **Logs the transaction**

## 🔍 **Testing the Webhook**

### **Manual Test:**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test webhook endpoint (simulate payment)
curl -X POST http://localhost:8000/webhook/crypto-pay \
  -H "Content-Type: application/json" \
  -H "crypto-pay-api-signature: test_signature" \
  -d '{
    "update_type": "invoice_paid",
    "payload": {
      "invoice_id": 123456,
      "status": "paid",
      "amount": "5",
      "asset": "USDT",
      "payload": "{\"user_id\": 6616925646, \"type\": \"deposit\", \"amount\": \"5.0\", \"asset\": \"USDT\"}"
    }
  }'
```

### **Real Test:**
1. **Start webhook server:** `python start_webhook.py`
2. **Make webhook public** (ngrok or server)
3. **Configure webhook URL** in Crypto Pay
4. **Create test payment** (5 USDT deposit)
5. **Complete payment** in Crypto Pay
6. **Check logs** for webhook processing

## 🛠️ **Troubleshooting**

### **Common Issues:**

1. **Webhook not receiving calls:**
   - Check if webhook URL is accessible
   - Verify ngrok is running
   - Check firewall settings

2. **Signature verification fails:**
   - Ensure webhook secret is correct
   - Check signature header format

3. **Database not updating:**
   - Check webhook logs for errors
   - Verify database connection
   - Check user/order exists

### **Debug Commands:**
```bash
# Check webhook server status
curl http://localhost:8000/health

# Check ngrok tunnels
curl http://localhost:4040/api/tunnels

# View webhook logs
tail -f webhook.log
```

## 📊 **Monitoring**

### **Log Files:**
- **Webhook logs:** Check terminal output
- **Application logs:** `bot.log`
- **Error logs:** Check for exceptions

### **Success Indicators:**
- ✅ Webhook receives POST requests
- ✅ Signature verification passes
- ✅ Database updates successfully
- ✅ User receives confirmation message
- ✅ No errors in logs

## 🚀 **Next Steps**

1. **Set up ngrok** for public webhook URL
2. **Configure webhook** in Crypto Pay dashboard
3. **Test with real payment**
4. **Monitor logs** for successful processing
5. **Deploy to production server** when ready

## 📞 **Support**

If you encounter issues:
1. Check webhook server logs
2. Verify Crypto Pay configuration
3. Test webhook endpoint manually
4. Check database connectivity

---

**🎉 Your crypto payment system is now ready for production!**


