"""Base repository class."""

from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from datetime import datetime

T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T]):
    """Base repository class with common CRUD operations."""
    
    def __init__(self, collection: AsyncIOMotorCollection, model_class: Type[T]):
        self.collection = collection
        self.model_class = model_class
    
    async def create(self, data: BaseModel) -> T:
        """Create a new document."""
        collection = self._get_collection() if hasattr(self, '_get_collection') else self.collection
        doc_data = data.dict(exclude_unset=True, by_alias=True)
        doc_data["created_at"] = datetime.utcnow()
        doc_data["updated_at"] = datetime.utcnow()
        
        result = await collection.insert_one(doc_data)
        created_doc = await collection.find_one({"_id": result.inserted_id})
        if created_doc and '_id' in created_doc:
            created_doc['_id'] = str(created_doc['_id'])
        return self.model_class(**created_doc)
    
    async def get_by_id(self, doc_id: str) -> Optional[T]:
        """Get document by ID."""
        try:
            object_id = ObjectId(doc_id)
            collection = self._get_collection() if hasattr(self, '_get_collection') else self.collection
            doc = await collection.find_one({"_id": object_id})
            if doc:
                doc['_id'] = str(doc['_id'])
                return self.model_class(**doc)
            return None
        except Exception:
            return None
    
    async def get_by_filter(self, filter_dict: Dict[str, Any]) -> Optional[T]:
        """Get single document by filter."""
        collection = self._get_collection() if hasattr(self, '_get_collection') else self.collection
        doc = await collection.find_one(filter_dict)
        if doc:
            # Convert ObjectId to string for Pydantic
            if '_id' in doc and doc['_id']:
                doc['_id'] = str(doc['_id'])
            return self.model_class(**doc)
        return None
    
    async def get_many(
        self,
        filter_dict: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        sort: List[tuple] = None
    ) -> List[T]:
        """Get multiple documents."""
        filter_dict = filter_dict or {}
        collection = self._get_collection() if hasattr(self, '_get_collection') else self.collection
        cursor = collection.find(filter_dict)
        
        if sort:
            cursor = cursor.sort(sort)
        
        cursor = cursor.skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        result = []
        for doc in docs:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            result.append(self.model_class(**doc))
        return result
    
    async def count(self, filter_dict: Dict[str, Any] = None) -> int:
        """Count documents."""
        filter_dict = filter_dict or {}
        collection = self._get_collection() if hasattr(self, '_get_collection') else self.collection
        return await collection.count_documents(filter_dict)
    
    async def update_by_id(self, doc_id: str, update_data: BaseModel) -> Optional[T]:
        """Update document by ID."""
        try:
            object_id = ObjectId(doc_id)
            update_dict = update_data.dict(exclude_unset=True, by_alias=True)
            update_dict["updated_at"] = datetime.utcnow()
            
            collection = self._get_collection() if hasattr(self, '_get_collection') else self.collection
            result = await collection.update_one(
                {"_id": object_id},
                {"$set": update_dict}
            )
            
            if result.modified_count:
                updated_doc = await collection.find_one({"_id": object_id})
                if updated_doc:
                    updated_doc['_id'] = str(updated_doc['_id'])
                    return self.model_class(**updated_doc)
            return None
        except Exception:
            return None
    
    async def update_by_filter(
        self,
        filter_dict: Dict[str, Any],
        update_data: Dict[str, Any]
    ) -> int:
        """Update multiple documents by filter."""
        update_data["updated_at"] = datetime.utcnow()
        collection = self._get_collection() if hasattr(self, '_get_collection') else self.collection
        result = await collection.update_many(
            filter_dict,
            {"$set": update_data}
        )
        return result.modified_count
    
    async def delete_by_id(self, doc_id: str) -> bool:
        """Delete document by ID."""
        try:
            object_id = ObjectId(doc_id)
            collection = self._get_collection() if hasattr(self, '_get_collection') else self.collection
            result = await collection.delete_one({"_id": object_id})
            return result.deleted_count > 0
        except Exception:
            return False
    
    async def delete_by_filter(self, filter_dict: Dict[str, Any]) -> int:
        """Delete multiple documents by filter."""
        collection = self._get_collection() if hasattr(self, '_get_collection') else self.collection
        result = await collection.delete_many(filter_dict)
        return result.deleted_count
    
    async def exists(self, filter_dict: Dict[str, Any]) -> bool:
        """Check if document exists."""
        collection = self._get_collection() if hasattr(self, '_get_collection') else self.collection
        doc = await collection.find_one(filter_dict, {"_id": 1})
        return doc is not None
