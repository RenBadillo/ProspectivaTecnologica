from app.database.user_repository import UserRepository

from app.models.user_profile import UserProfile


repo = UserRepository()

usuario = UserProfile(

    id=None,

    whatsapp_number="5215561310892",

    name="Renata",

    age=22,

    sex="female",

    weight=60,

    height=1.65,

    activity_level="moderate",

    goal="muscle_gain",

    dietary_restrictions=[],

    food_preferences=["pollo", "fruta"],

    budget=1500
)

repo.create(usuario)

resultado = repo.get_by_whatsapp(
    "5215512345678"
)

print(resultado)