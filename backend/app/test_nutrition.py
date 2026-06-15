from app.models.user_profile import UserProfile

from app.services.nutrition_service import (
    NutritionService
)


user = UserProfile(

    id=1,

    whatsapp_number="5215512345678",

    name="Renata",

    age=22,

    sex="female",

    weight=60,

    height=1.65,

    activity_level="moderate",

    goal="muscle_gain",

    dietary_restrictions=[],

    food_preferences=[],

    budget=1500
)

service = NutritionService()

profile = service.generate_profile(
    user
)

print(profile)