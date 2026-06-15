from app.models.nutrition_profile import NutritionProfile


class MealPlanService:

    def generate_text_meal_plan(
        self,
        nutrition_profile: NutritionProfile,
        inventory: list[dict],
        goal: str
    ) -> str:

        available = [
            item["name"].lower()
            for item in inventory
            if item.get("quantity", 0) > 0
        ]

        protein = self._choose_first(
            available,
            [
                "pechuga de pollo",
                "pollo",
                "lata de atún",
                "atun",
                "atún",
                "huevo"
            ],
            "proteína disponible"
        )

        carb = self._choose_first(
            available,
            [
                "arroz cocido",
                "arroz",
                "paquete de arroz",
                "pasta",
                "avena"
            ],
            "carbohidrato disponible"
        )

        vegetable = self._choose_first(
            available,
            [
                "zanahoria",
                "brócoli",
                "brocoli",
                "espinaca",
                "lechuga"
            ],
            "verdura disponible"
        )

        breakfast = self._breakfast(available)
        lunch = f"{protein} con {carb} y {vegetable}"
        dinner = f"{protein} ligero con {vegetable}"
        snack = self._snack(available)

        if goal == "weight_loss":
            strategy = (
                "Plan enfocado en saciedad, proteína suficiente "
                "y porciones moderadas."
            )
        elif goal == "muscle_gain":
            strategy = (
                "Plan enfocado en proteína suficiente y energía "
                "para recuperación muscular."
            )
        else:
            strategy = (
                "Plan equilibrado basado en los alimentos disponibles."
            )

        daily_calories = round(
            nutrition_profile.calories_target
        )

        breakfast_cal = round(daily_calories * 0.25)
        lunch_cal = round(daily_calories * 0.35)
        dinner_cal = round(daily_calories * 0.30)
        snack_cal = round(daily_calories * 0.10)

        days = [
            "Lunes",
            "Martes",
            "Miércoles",
            "Jueves",
            "Viernes",
            "Sábado",
            "Domingo"
        ]

        response = (
            "Plan semanal sugerido\n\n"
            f"Objetivo: {goal}\n"
            f"Calorías diarias aproximadas: {daily_calories} kcal\n"
            f"Proteínas objetivo: {nutrition_profile.protein_target} g\n\n"
            f"Estrategia: {strategy}\n\n"
        )

        for day in days:
            response += (
                f"{day}\n"
                f"- Desayuno ({breakfast_cal} kcal aprox): {breakfast}\n"
                f"- Comida ({lunch_cal} kcal aprox): {lunch}\n"
                f"- Cena ({dinner_cal} kcal aprox): {dinner}\n"
                f"- Snack ({snack_cal} kcal aprox): {snack}\n\n"
            )

        response += (
            "Nota: este plan usa principalmente tu inventario actual. "
            "Puedes pedirme una receta específica para cualquiera de estas comidas."
        )

        return response.strip()

    def _choose_first(
        self,
        available: list[str],
        options: list[str],
        fallback: str
    ) -> str:

        for option in options:
            if option in available:
                return option

        return fallback

    def _breakfast(
        self,
        available: list[str]
    ) -> str:

        if "huevo" in available:
            return "huevo con zanahoria o verdura disponible"

        if "avena" in available:
            return "avena preparada con fruta disponible"

        return "desayuno con alimento disponible alto en proteína"

    def _snack(
        self,
        available: list[str]
    ) -> str:

        if "huevo" in available:
            return "huevo cocido"

        if "manzana" in available:
            return "manzana"

        if "lata de atún" in available:
            return "atún en porción pequeña"

        return "colación ligera con alimento disponible"