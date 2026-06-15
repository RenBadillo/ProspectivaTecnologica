from dataclasses import dataclass


@dataclass
class ShoppingItem:

    name: str

    quantity: float

    unit: str

    priority: str

    reason: str