from app.models.user_profile import UserProfile
from app.models.nutrition_profile import NutritionProfile


class NutritionService:

    ACTIVITY_FACTORS = {

        "sedentary": 1.2,

        "light": 1.375,

        "moderate": 1.55,

        "active": 1.725,

        "very_active": 1.9
    }

    def calculate_tmb(
        self,
        user: UserProfile
    ) -> float:

        # Acepta altura en metros (1.65) o centímetros (165).
        height_cm = user.height * 100 if user.height <= 3 else user.height

        if user.sex.lower() == "male":

            return (
                (10 * user.weight)
                + (6.25 * height_cm)
                - (5 * user.age)
                + 5
            )

        return (
            (10 * user.weight)
            + (6.25 * height_cm)
            - (5 * user.age)
            - 161
        )

    def calculate_get(
        self,
        tmb: float,
        activity_level: str
    ) -> float:

        factor = self.ACTIVITY_FACTORS.get(
            activity_level,
            1.2
        )

        return tmb * factor

    def calculate_target_calories(
        self,
        get: float,
        goal: str
    ) -> float:

        goal = goal.lower()

        if goal == "fat_loss":

            return get * 0.8

        if goal == "muscle_gain":

            return get * 1.1

        return get

    def calculate_protein(
        self,
        user: UserProfile
    ) -> float:

        if user.goal.lower() in [
            "fat_loss",
            "muscle_gain"
        ]:

            return user.weight * 2.0

        return user.weight * 1.6

    def calculate_fat(
        self,
        user: UserProfile
    ) -> float:

        return user.weight * 0.8

    def calculate_carbs(
        self,
        calories_target: float,
        protein_g: float,
        fat_g: float
    ) -> float:

        protein_calories = protein_g * 4

        fat_calories = fat_g * 9

        remaining_calories = (
            calories_target
            - protein_calories
            - fat_calories
        )

        return remaining_calories / 4

    def generate_profile(
        self,
        user: UserProfile
    ) -> NutritionProfile:

        tmb = self.calculate_tmb(user)

        get = self.calculate_get(
            tmb,
            user.activity_level
        )

        calories_target = (
            self.calculate_target_calories(
                get,
                user.goal
            )
        )

        protein = self.calculate_protein(
            user
        )

        fat = self.calculate_fat(
            user
        )

        carbs = self.calculate_carbs(
            calories_target,
            protein,
            fat
        )

        return NutritionProfile(

            tmb=round(tmb, 2),

            get=round(get, 2),

            calories_target=round(
                calories_target,
                2
            ),

            protein_target=round(
                protein,
                2
            ),

            fat_target=round(
                fat,
                2
            ),

            carb_target=round(
                carbs,
                2
            )
        )