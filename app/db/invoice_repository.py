"""Invoice repository for managing invoice data."""

import logging
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.invoice import Invoice, InvoiceCreate, InvoiceUpdate, InvoiceStatus

logger = logging.getLogger(__name__)


class InvoiceRepository:
    """Repository for invoice data operations."""
    
    def __init__(self, collection: Optional[AsyncIOMotorCollection] = None):
        """Initialize repository."""
        self.collection = collection
    
    def _get_collection(self) -> AsyncIOMotorCollection:
        """Get the invoice collection."""
        if self.collection is None:
            from app.db import db
            self.collection = db.db.invoices
        return self.collection
    
    def _utcnow(self) -> datetime:
        """Get current UTC datetime."""
        return datetime.utcnow()
    
    async def create_invoice(self, invoice_data: InvoiceCreate) -> Optional[Invoice]:
        """Create a new invoice."""
        try:
            collection = self._get_collection()
            
            invoice_dict = invoice_data.model_dump(by_alias=True)
            invoice_dict.update({
                "status": InvoiceStatus.PENDING,
                "created_at": self._utcnow(),
                "updated_at": self._utcnow()
            })
            
            result = await collection.insert_one(invoice_dict)
            
            # Get created invoice
            invoice_doc = await collection.find_one({"_id": result.inserted_id})
            if invoice_doc:
                invoice_doc["_id"] = str(invoice_doc["_id"])
                return Invoice(**invoice_doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            return None
    
    async def get_by_invoice_id(self, invoice_id: int) -> Optional[Invoice]:
        """Get invoice by Crypto Pay invoice ID."""
        try:
            collection = self._get_collection()
            invoice_doc = await collection.find_one({"invoice_id": invoice_id})
            
            if invoice_doc:
                invoice_doc["_id"] = str(invoice_doc["_id"])
                return Invoice(**invoice_doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting invoice by ID {invoice_id}: {e}")
            return None
    
    async def get_by_user_id(self, user_id: int, limit: int = 50) -> List[Invoice]:
        """Get invoices by user ID."""
        try:
            collection = self._get_collection()
            cursor = collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
            
            invoices = []
            async for invoice_doc in cursor:
                invoice_doc["_id"] = str(invoice_doc["_id"])
                invoices.append(Invoice(**invoice_doc))
            
            return invoices
            
        except Exception as e:
            logger.error(f"Error getting invoices for user {user_id}: {e}")
            return []
    
    async def update_invoice(self, invoice_id: int, update_data: InvoiceUpdate) -> Optional[Invoice]:
        """Update invoice by Crypto Pay invoice ID."""
        try:
            collection = self._get_collection()
            
            update_dict = update_data.model_dump(exclude_unset=True, by_alias=True)
            if update_dict:
                update_dict["updated_at"] = self._utcnow()
                
                result = await collection.update_one(
                    {"invoice_id": invoice_id},
                    {"$set": update_dict}
                )
                
                if result.modified_count > 0:
                    return await self.get_by_invoice_id(invoice_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating invoice {invoice_id}: {e}")
            return None
    
    async def mark_as_paid(
        self, 
        invoice_id: int, 
        paid_amount: str,
        paid_asset: str,
        paid_usd_rate: Optional[str] = None,
        fee_amount: Optional[float] = None,
        fee_asset: Optional[str] = None,
        is_swapped: bool = False,
        swapped_to: Optional[str] = None,
        swapped_amount: Optional[str] = None,
        swapped_rate: Optional[str] = None,
        paid_at: Optional[datetime] = None
    ) -> Optional[Invoice]:
        """Mark invoice as paid with payment details."""
        try:
            update_data = InvoiceUpdate(
                status=InvoiceStatus.PAID,
                paid_amount=paid_amount,
                paid_asset=paid_asset,
                paid_usd_rate=paid_usd_rate,
                fee_amount=fee_amount,
                fee_asset=fee_asset,
                is_swapped=is_swapped,
                swapped_to=swapped_to,
                swapped_amount=swapped_amount,
                swapped_rate=swapped_rate,
                paid_at=paid_at or self._utcnow()
            )
            
            return await self.update_invoice(invoice_id, update_data)
            
        except Exception as e:
            logger.error(f"Error marking invoice {invoice_id} as paid: {e}")
            return None
    
    async def mark_as_expired(self, invoice_id: int) -> Optional[Invoice]:
        """Mark invoice as expired."""
        try:
            update_data = InvoiceUpdate(status=InvoiceStatus.EXPIRED)
            return await self.update_invoice(invoice_id, update_data)
            
        except Exception as e:
            logger.error(f"Error marking invoice {invoice_id} as expired: {e}")
            return None
    
    async def get_pending_invoices(self, user_id: Optional[int] = None) -> List[Invoice]:
        """Get pending invoices, optionally filtered by user."""
        try:
            collection = self._get_collection()
            
            query = {"status": InvoiceStatus.PENDING}
            if user_id:
                query["user_id"] = user_id
            
            cursor = collection.find(query).sort("created_at", -1)
            
            invoices = []
            async for invoice_doc in cursor:
                invoice_doc["_id"] = str(invoice_doc["_id"])
                invoices.append(Invoice(**invoice_doc))
            
            return invoices
            
        except Exception as e:
            logger.error(f"Error getting pending invoices: {e}")
            return []
    
    async def cleanup_expired_invoices(self) -> int:
        """Clean up expired invoices."""
        try:
            collection = self._get_collection()
            
            # Mark invoices as expired if they're past expiration time
            current_time = self._utcnow()
            result = await collection.update_many(
                {
                    "status": InvoiceStatus.PENDING,
                    "expires_at": {"$lt": current_time}
                },
                {
                    "$set": {
                        "status": InvoiceStatus.EXPIRED,
                        "updated_at": current_time
                    }
                }
            )
            
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired invoices: {e}")
            return 0


# Global repository instance
invoice_repo = InvoiceRepository()
