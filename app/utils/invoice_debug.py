"""Invoice debugging utilities."""

import asyncio
import logging
from typing import List, Optional
from app.db.invoice_repository import invoice_repo
from app.models.invoice import InvoiceStatus

logger = logging.getLogger(__name__)


async def get_user_invoices(user_id: int, limit: int = 10) -> List[dict]:
    """Get and format user invoices for debugging."""
    try:
        invoices = await invoice_repo.get_by_user_id(user_id, limit)
        result = []
        
        for invoice in invoices:
            result.append({
                "invoice_id": invoice.invoice_id,
                "type": invoice.type,
                "status": invoice.status,
                "amount": f"{invoice.amount} {invoice.asset}",
                "paid_amount": f"{invoice.paid_amount} {invoice.paid_asset}" if invoice.paid_amount else None,
                "created_at": invoice.created_at.isoformat(),
                "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None,
                "order_id": invoice.order_id,
                "fee": f"{invoice.fee_amount} {invoice.fee_asset}" if invoice.fee_amount else None,
                "swap_info": f"Swapped to {invoice.swapped_amount} {invoice.swapped_to}" if invoice.is_swapped else None
            })
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting user invoices: {e}")
        return []


async def get_invoice_summary() -> dict:
    """Get invoice summary statistics."""
    try:
        pending_invoices = await invoice_repo.get_pending_invoices()
        
        # Count by status and type
        stats = {
            "total_pending": len(pending_invoices),
            "by_type": {},
            "recent_paid": 0
        }
        
        for invoice in pending_invoices:
            inv_type = invoice.type
            if inv_type not in stats["by_type"]:
                stats["by_type"][inv_type] = 0
            stats["by_type"][inv_type] += 1
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting invoice summary: {e}")
        return {}


async def debug_invoice_by_id(invoice_id: int) -> Optional[dict]:
    """Get detailed invoice information for debugging."""
    try:
        invoice = await invoice_repo.get_by_invoice_id(invoice_id)
        if not invoice:
            return None
        
        return {
            "invoice_id": invoice.invoice_id,
            "user_id": invoice.user_id,
            "type": invoice.type,
            "status": invoice.status,
            "original_amount": f"{invoice.amount} {invoice.asset}",
            "paid_amount": f"{invoice.paid_amount} {invoice.paid_asset}" if invoice.paid_amount else None,
            "usd_rate": invoice.paid_usd_rate,
            "fee": {
                "amount": invoice.fee_amount,
                "asset": invoice.fee_asset
            } if invoice.fee_amount else None,
            "swap": {
                "is_swapped": invoice.is_swapped,
                "to_asset": invoice.swapped_to,
                "amount": invoice.swapped_amount,
                "rate": invoice.swapped_rate
            } if invoice.is_swapped else None,
            "timestamps": {
                "created": invoice.created_at.isoformat(),
                "paid": invoice.paid_at.isoformat() if invoice.paid_at else None,
                "expires": invoice.expires_at.isoformat() if invoice.expires_at else None
            },
            "order_id": invoice.order_id,
            "urls": {
                "bot_url": invoice.bot_invoice_url,
                "mini_app_url": invoice.mini_app_invoice_url
            }
        }
    
    except Exception as e:
        logger.error(f"Error debugging invoice {invoice_id}: {e}")
        return None


async def cleanup_expired_invoices() -> int:
    """Clean up expired invoices and return count."""
    try:
        count = await invoice_repo.cleanup_expired_invoices()
        logger.info(f"Cleaned up {count} expired invoices")
        return count
    except Exception as e:
        logger.error(f"Error cleaning up expired invoices: {e}")
        return 0


if __name__ == "__main__":
    # Example usage
    async def main():
        from app.db import db
        await db.connect()
        
        # Get invoice summary
        summary = await get_invoice_summary()
        print("Invoice Summary:", summary)
        
        # Get user invoices
        user_invoices = await get_user_invoices(6616925646)
        print("User Invoices:", user_invoices)
        
        await db.disconnect()
    
    asyncio.run(main())
