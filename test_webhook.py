#!/usr/bin/env python3
"""Test Crypto Pay webhook endpoint."""

import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_webhook():
    """Test the webhook endpoint."""
    try:
        # Webhook URL
        url = "http://localhost:8000/webhook/crypto-pay"
        
        # Test data (simulated payment)
        webhook_data = {
            "update_type": "invoice_paid",
            "payload": {
                "invoice_id": 123456,
                "status": "paid",
                "amount": "5",
                "asset": "USDT",
                "payload": json.dumps({
                    "user_id": 6616925646,
                    "type": "deposit",
                    "amount": "5.0",
                    "asset": "USDT"
                })
            }
        }
        
        # Headers
        headers = {
            "Content-Type": "application/json",
            "crypto-pay-api-signature": "test_signature"
        }
        
        logger.info("🧪 Testing webhook endpoint...")
        logger.info(f"📡 URL: {url}")
        logger.info(f"📦 Data: {json.dumps(webhook_data, indent=2)}")
        
        # Send request
        response = requests.post(url, json=webhook_data, headers=headers)
        
        logger.info(f"📊 Response Status: {response.status_code}")
        logger.info(f"📄 Response Body: {response.text}")
        
        if response.status_code == 200:
            logger.info("✅ Webhook test successful!")
        else:
            logger.warning(f"⚠️ Webhook test failed with status {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Error testing webhook: {e}")

def test_health():
    """Test health endpoint."""
    try:
        url = "http://localhost:8000/health"
        response = requests.get(url)
        
        logger.info(f"💚 Health check: {response.status_code} - {response.text}")
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    print("🔗 Testing Crypto Pay Webhook")
    print("=" * 40)
    
    # Test health first
    test_health()
    print()
    
    # Test webhook
    test_webhook()


