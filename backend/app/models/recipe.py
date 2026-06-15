from dataclasses import dataclass, field

from app.models.recipe_ingredient import (
    RecipeIngredient
)

@dataclass
class Recipe:

    name: str

    description: str

    ingredients: list[
        RecipeIngredient
    ] = field(default_factory=list)

    instructions: list[str] = field(
        default_factory=list
    )

    calories: float = 0

    protein: float = 0

    carbs: float = 0

    fats: float = 0

    servings: int = 1

    preparation_time: int = 0

    cooking_time: int = 0

    difficulty: str = "Easy"