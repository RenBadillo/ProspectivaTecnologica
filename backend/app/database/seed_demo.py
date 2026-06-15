from app.database.create_db import create_database
from app.database.connection import get_connection
from app.database.user_repository import UserRepository
from app.models.user_profile import UserProfile


def seed_demo_data():
    create_database()
    user = UserProfile(
        id=None,
        whatsapp_number="5215512345678",
        name="Renata",
        age=22,
        sex="female",
        weight=60,
        height=1.65,
        activity_level="moderate",
        goal="muscle_gain",
        dietary_restrictions=[],
        food_preferences=["pollo", "arroz", "fruta"],
        budget=1500,
    )
    UserRepository().create(user)

    conn = get_connection()
    cursor = conn.cursor()
    foods = [
        ("pollo", 1, "seed"),
        ("arroz", 2, "seed"),
        ("zanahoria", 3, "seed"),
        ("huevo", 4, "seed"),
    ]
    for name, quantity, source in foods:
        cursor.execute(
            """
            INSERT INTO inventory(name, quantity, source)
            VALUES (?, ?, ?)
            ON CONFLICT(name)
            DO UPDATE SET
                quantity = excluded.quantity,
                source = excluded.source,
                last_update = CURRENT_TIMESTAMP
            """,
            (name, quantity, source),
        )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    seed_demo_data()
    print("Datos demo cargados")
