from dataclasses import dataclass, field

from app.models.shopping_item import (
    ShoppingItem
)


@dataclass
class ShoppingList:

    items: list[
        ShoppingItem
    ] = field(default_factory=list)