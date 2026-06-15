from dataclasses import dataclass


@dataclass
class NutritionProfile:

    tmb: float

    get: float

    calories_target: float

    protein_target: float

    fat_target: float

    carb_target: float