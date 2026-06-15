from dataclasses import dataclass, field

from app.models.meal import Meal


@dataclass
class DailyPlan:

    breakfast: Meal

    lunch: Meal

    dinner: Meal

    snacks: list[Meal] = field(
        default_factory=list
    )


@dataclass
class MealPlan:

    days: dict[str, DailyPlan]