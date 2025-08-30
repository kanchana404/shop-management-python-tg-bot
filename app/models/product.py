"""Product model and schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class City(str, Enum):
    """Supported cities."""
    BELGRADE = "Belgrade"
    NOVI_SAD = "Novi Sad"
    PANCEVO = "Pančevo"


class Area(str, Enum):
    """Supported areas."""
    # Belgrade areas
    VRACAR = "Vracar"
    NOVI_BEOGRAD = "Novi Beograd"
    STARI_GRAD = "Stari grad"
    ZVEZDARA = "Zvezdara"
    VOZDOVAC = "Vozdovac"
    KONJARNIK = "Konjarnik"
    SAVSKI_VENAC = "Savski venac"
    BANOVO_BRDO = "Banovo brdo"
    MIRIJEVO = "Mirijevo"
    ZEMUN = "Zemun"
    ADA_CIGANLIJA = "Ada Ciganlija"
    PALILULA = "Palilula"
    SENJAK = "Senjak"
    KARABURMA = "Karaburma"
    BORCA = "Borca"
    
    # Novi Sad areas
    CENTAR_NS = "Centar"
    PODBARA = "Podbara"
    PETROVARADIN = "Petrovaradin"
    DETELINARA = "Detelinara"
    
    # Pančevo areas
    CENTAR_PANCEVO = "Centar"


# Mapping cities to their areas
CITY_AREAS = {
    City.BELGRADE: [
        Area.VRACAR, Area.NOVI_BEOGRAD, Area.STARI_GRAD, Area.ZVEZDARA,
        Area.VOZDOVAC, Area.KONJARNIK, Area.SAVSKI_VENAC, Area.BANOVO_BRDO,
        Area.MIRIJEVO, Area.ZEMUN, Area.ADA_CIGANLIJA, Area.PALILULA,
        Area.SENJAK, Area.KARABURMA, Area.BORCA
    ],
    City.NOVI_SAD: [
        Area.CENTAR_NS, Area.PODBARA, Area.PETROVARADIN, Area.DETELINARA
    ],
    City.PANCEVO: [
        Area.CENTAR_PANCEVO
    ]
}


class Product(BaseModel):
    """Product model."""
    id: Optional[str] = Field(None, alias="_id")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    photos: List[str] = Field(default_factory=list, description="Product photo URLs/file_ids")
    price: float = Field(..., description="Product price in EUR")
    quantity: int = Field(default=0, description="Available quantity")
    city: City = Field(..., description="City where product is available")
    area: Area = Field(..., description="Area where product is available")
    is_active: bool = Field(default=True, description="Whether product is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic config."""
        populate_by_name = True
        use_enum_values = True


class ProductCreate(BaseModel):
    """Schema for creating a product."""
    name: str
    description: str
    photos: List[str] = []
    price: float
    quantity: int = 0
    city: City
    area: Area
    is_active: bool = True


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = None
    description: Optional[str] = None
    photos: Optional[List[str]] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    city: Optional[City] = None
    area: Optional[Area] = None
    is_active: Optional[bool] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProductFilter(BaseModel):
    """Schema for filtering products."""
    city: Optional[City] = None
    area: Optional[Area] = None
    is_active: Optional[bool] = True
    name_search: Optional[str] = None
