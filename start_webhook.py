#!/usr/bin/env python3
"""Start Crypto Pay webhook server."""

import uvicorn
import logging
from app.webhooks.crypto_pay_webhook import app
from app.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Start the webhook server."""
    try:
        logger.info("🚀 Starting Crypto Pay Webhook Server...")
        logger.info(f"📊 Environment: {settings.environment}")
        logger.info(f"🔗 Webhook URL: http://localhost:8000/webhook/crypto-pay")
        logger.info(f"💚 Health Check: http://localhost:8000/health")
        
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Webhook server stopped by user")
    except Exception as e:
        logger.error(f"❌ Error starting webhook server: {e}")

if __name__ == "__main__":
    main()


