from dataclasses import dataclass


@dataclass
class RecipeIngredient:

    name: str

    quantity: float

    unit: str