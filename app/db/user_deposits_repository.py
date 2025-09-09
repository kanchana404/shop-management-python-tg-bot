"""User deposits repository for managing cumulative deposit data."""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.user_deposits import UserDeposits, UserDepositsUpdate, DepositTransaction

logger = logging.getLogger(__name__)


class UserDepositsRepository:
    """Repository for user deposits data operations."""
    
    def __init__(self, collection: Optional[AsyncIOMotorCollection] = None):
        """Initialize repository."""
        self.collection = collection
    
    def _get_collection(self) -> AsyncIOMotorCollection:
        """Get the user_deposits collection."""
        if self.collection is None:
            from app.db import db
            self.collection = db.db.user_deposits
        return self.collection
    
    def _utcnow(self) -> datetime:
        """Get current UTC datetime."""
        return datetime.utcnow()
    
    async def get_or_create_user_deposits(self, user_id: int) -> Optional[UserDeposits]:
        """Get or create user deposits record."""
        try:
            collection = self._get_collection()
            
            # Try to find existing record
            user_deposits_doc = await collection.find_one({"user_id": user_id})
            
            if user_deposits_doc:
                user_deposits_doc["_id"] = str(user_deposits_doc["_id"])
                return UserDeposits(**user_deposits_doc)
            
            # Create new record if doesn't exist
            new_user_deposits = UserDeposits(
                user_id=user_id,
                total_deposits_count=0,
                total_deposited_usdt=0.0,
                total_fees_paid=0.0,
                assets_deposited={},
                transactions=[],
                created_at=self._utcnow(),
                updated_at=self._utcnow()
            )
            
            user_deposits_dict = new_user_deposits.model_dump(by_alias=True, exclude={"id"})
            result = await collection.insert_one(user_deposits_dict)
            
            # Get created record
            created_doc = await collection.find_one({"_id": result.inserted_id})
            if created_doc:
                created_doc["_id"] = str(created_doc["_id"])
                return UserDeposits(**created_doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting/creating user deposits for user {user_id}: {e}")
            return None
    
    async def add_deposit_transaction(
        self,
        user_id: int,
        invoice_id: int,
        amount: str,
        asset: str,
        paid_amount: Optional[str] = None,
        paid_asset: Optional[str] = None,
        usd_rate: Optional[str] = None,
        fee_amount: Optional[float] = None,
        fee_asset: Optional[str] = None,
        is_swapped: bool = False,
        swapped_details: Optional[Dict[str, Any]] = None
    ) -> Optional[UserDeposits]:
        """Add a new deposit transaction and update cumulative totals."""
        try:
            collection = self._get_collection()
            
            # Get or create user deposits record
            user_deposits = await self.get_or_create_user_deposits(user_id)
            if not user_deposits:
                logger.error(f"Failed to get/create user deposits for user {user_id}")
                return None
            
            # Create transaction record
            transaction = DepositTransaction(
                invoice_id=invoice_id,
                amount=amount,
                asset=asset,
                paid_amount=paid_amount,
                paid_asset=paid_asset,
                usd_rate=usd_rate,
                fee_amount=fee_amount,
                fee_asset=fee_asset,
                is_swapped=is_swapped,
                swapped_details=swapped_details,
                deposit_date=self._utcnow()
            )
            
            # Calculate USDT equivalent amount
            final_amount = float(paid_amount) if paid_amount else float(amount)
            final_asset = paid_asset if paid_asset else asset
            
            # For simplicity, assume 1:1 USDT conversion for now
            # In production, you might want to use exchange rates
            usdt_equivalent = final_amount
            
            # Update cumulative totals
            new_total_count = user_deposits.total_deposits_count + 1
            new_total_usdt = user_deposits.total_deposited_usdt + usdt_equivalent
            new_total_fees = user_deposits.total_fees_paid + (fee_amount or 0.0)
            
            # Update assets_deposited
            updated_assets = user_deposits.assets_deposited.copy()
            if final_asset not in updated_assets:
                updated_assets[final_asset] = 0.0
            updated_assets[final_asset] += final_amount
            
            # Update statistics
            current_time = self._utcnow()
            first_deposit = user_deposits.first_deposit_date or current_time
            
            largest_amount = user_deposits.largest_deposit_amount
            largest_invoice = user_deposits.largest_deposit_invoice
            if usdt_equivalent > largest_amount:
                largest_amount = usdt_equivalent
                largest_invoice = invoice_id
            
            # Add transaction to list
            updated_transactions = user_deposits.transactions.copy()
            updated_transactions.append(transaction)
            
            # Update the record
            update_data = {
                "$set": {
                    "total_deposits_count": new_total_count,
                    "total_deposited_usdt": new_total_usdt,
                    "total_fees_paid": new_total_fees,
                    "assets_deposited": updated_assets,
                    "first_deposit_date": first_deposit,
                    "last_deposit_date": current_time,
                    "largest_deposit_amount": largest_amount,
                    "largest_deposit_invoice": largest_invoice,
                    "updated_at": current_time
                },
                "$push": {
                    "transactions": transaction.model_dump()
                }
            }
            
            result = await collection.update_one(
                {"user_id": user_id},
                update_data
            )
            
            if result.modified_count > 0:
                # Get updated record
                updated_doc = await collection.find_one({"user_id": user_id})
                if updated_doc:
                    updated_doc["_id"] = str(updated_doc["_id"])
                    logger.info(f"Deposit transaction added: User {user_id}, Amount {final_amount} {final_asset}")
                    return UserDeposits(**updated_doc)
            
            logger.error(f"Failed to update user deposits for user {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error adding deposit transaction for user {user_id}: {e}")
            return None
    
    async def get_user_deposits(self, user_id: int) -> Optional[UserDeposits]:
        """Get user deposits record."""
        try:
            collection = self._get_collection()
            user_deposits_doc = await collection.find_one({"user_id": user_id})
            
            if user_deposits_doc:
                user_deposits_doc["_id"] = str(user_deposits_doc["_id"])
                return UserDeposits(**user_deposits_doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user deposits for user {user_id}: {e}")
            return None
    
    async def get_user_deposit_summary(self, user_id: int) -> Dict[str, Any]:
        """Get user deposit summary for display."""
        try:
            user_deposits = await self.get_user_deposits(user_id)
            if not user_deposits:
                return {
                    "total_deposits": 0,
                    "total_amount": "0.00 USDT",
                    "total_fees": "0.00 USDT",
                    "assets_breakdown": {},
                    "first_deposit": None,
                    "last_deposit": None,
                    "largest_deposit": "0.00 USDT"
                }
            
            return {
                "total_deposits": user_deposits.total_deposits_count,
                "total_amount": f"{user_deposits.total_deposited_usdt:.2f} USDT",
                "total_fees": f"{user_deposits.total_fees_paid:.2f} USDT",
                "assets_breakdown": {
                    asset: f"{amount:.2f} {asset}" 
                    for asset, amount in user_deposits.assets_deposited.items()
                },
                "first_deposit": user_deposits.first_deposit_date.isoformat() if user_deposits.first_deposit_date else None,
                "last_deposit": user_deposits.last_deposit_date.isoformat() if user_deposits.last_deposit_date else None,
                "largest_deposit": f"{user_deposits.largest_deposit_amount:.2f} USDT",
                "recent_transactions": [
                    {
                        "invoice_id": tx.invoice_id,
                        "amount": f"{tx.paid_amount or tx.amount} {tx.paid_asset or tx.asset}",
                        "date": tx.deposit_date.isoformat(),
                        "fee": f"{tx.fee_amount} {tx.fee_asset}" if tx.fee_amount else "0.00"
                    }
                    for tx in sorted(user_deposits.transactions, key=lambda x: x.deposit_date, reverse=True)[:5]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting user deposit summary for user {user_id}: {e}")
            return {}
    
    async def get_all_users_deposits_stats(self) -> Dict[str, Any]:
        """Get statistics for all user deposits."""
        try:
            collection = self._get_collection()
            
            # Aggregate stats
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_users": {"$sum": 1},
                        "total_deposits_count": {"$sum": "$total_deposits_count"},
                        "total_volume_usdt": {"$sum": "$total_deposited_usdt"},
                        "total_fees_collected": {"$sum": "$total_fees_paid"},
                        "avg_deposits_per_user": {"$avg": "$total_deposits_count"},
                        "avg_amount_per_user": {"$avg": "$total_deposited_usdt"}
                    }
                }
            ]
            
            result = await collection.aggregate(pipeline).to_list(1)
            
            if result:
                stats = result[0]
                return {
                    "total_users_with_deposits": stats.get("total_users", 0),
                    "total_deposits_count": stats.get("total_deposits_count", 0),
                    "total_volume": f"{stats.get('total_volume_usdt', 0):.2f} USDT",
                    "total_fees": f"{stats.get('total_fees_collected', 0):.2f} USDT",
                    "avg_deposits_per_user": f"{stats.get('avg_deposits_per_user', 0):.1f}",
                    "avg_amount_per_user": f"{stats.get('avg_amount_per_user', 0):.2f} USDT"
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting deposits stats: {e}")
            return {}


# Global repository instance
user_deposits_repo = UserDepositsRepository()
