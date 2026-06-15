from enum import Enum


class Goal(str, Enum):

    WEIGHT_LOSS = "weight_loss"

    MUSCLE_GAIN = "muscle_gain"

    MAINTENANCE = "maintenance"

    RECOMPOSITION = "recomposition"


class ActivityLevel(str, Enum):

    SEDENTARY = "sedentary"

    LIGHT = "light"

    MODERATE = "moderate"

    ACTIVE = "active"

    VERY_ACTIVE = "very_active"