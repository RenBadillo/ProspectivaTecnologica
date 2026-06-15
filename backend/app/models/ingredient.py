from dataclasses import dataclass
from typing import Optional


@dataclass
class Ingredient:
    name: str
    quantity: float
    unit: str

    category: Optional[str] = None

    expiration_date: Optional[str] = None

    barcode: Optional[str] = None

    estimated_calories_per_100g: Optional[float] = None