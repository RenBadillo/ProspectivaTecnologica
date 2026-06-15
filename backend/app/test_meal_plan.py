from app.services.meal_plan_service import (
    MealPlanService
)

from app.models.enums import Goal


service = MealPlanService()

meal_plan = service.generate_meal_plan(
    calories_target=2200,
    goal=Goal.MUSCLE_GAIN
)

for day, plan in meal_plan.days.items():

    print("\n", day.upper())

    print(
        "Breakfast:",
        plan.breakfast.recipe.calories
    )

    print(
        "Lunch:",
        plan.lunch.recipe.calories
    )

    print(
        "Dinner:",
        plan.dinner.recipe.calories
    )

    print(
        "Snack:",
        plan.snacks[0].recipe.calories
    )