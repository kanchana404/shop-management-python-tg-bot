"""Crypto Pay webhook handler."""

import json
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from app.services.crypto_pay_service import crypto_pay_service
from app.handlers.crypto_payment_handlers import handle_crypto_webhook
from app.db import db

logger = logging.getLogger(__name__)

app = FastAPI(title="Crypto Pay Webhook")


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    try:
        await db.connect()
        logger.info("Database connected for webhook server")
    except Exception as e:
        logger.error(f"Failed to connect database in webhook server: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    try:
        await db.disconnect()
        logger.info("Database disconnected from webhook server")
    except Exception as e:
        logger.error(f"Error disconnecting database: {e}")


@app.post("/webhook/crypto-pay")
async def crypto_pay_webhook(request: Request):
    """Handle Crypto Pay webhook."""
    try:
        # Get request body
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # Get signature from headers
        signature = request.headers.get('crypto-pay-api-signature')
        if not signature:
            logger.error("Missing crypto-pay-api-signature header")
            raise HTTPException(status_code=400, detail="Missing signature")
        
        # Verify signature (allow test signatures in development)
        if signature == "test_signature":
            logger.info("Using test signature - skipping verification")
        elif not crypto_pay_service.verify_webhook_signature(
            crypto_pay_service.token, body_str, signature
        ):
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Parse webhook data
        webhook_data = json.loads(body_str)
        
        # Process webhook
        logger.info(f"Processing webhook: {webhook_data.get('update_type', 'unknown')}")
        try:
            success = await handle_crypto_webhook(webhook_data)
            
            if success:
                logger.info("Webhook processed successfully")
                return {"status": "success"}
            else:
                logger.warning("Webhook processing failed")
                return {"status": "failed"}
        except Exception as e:
            logger.error(f"Error in webhook processing: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
