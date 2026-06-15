import json
from typing import Optional

from app.database.connection import get_connection
from app.models.user_profile import UserProfile


class UserRepository:
    def create(self, user: UserProfile):
        """Crea o actualiza un usuario usando whatsapp_number como llave única."""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO users (
                whatsapp_number,
                nombre,
                edad,
                sexo,
                peso,
                altura,
                activity_level,
                objetivo,
                dietary_restrictions,
                food_preferences,
                budget
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(whatsapp_number)
            DO UPDATE SET
                nombre = excluded.nombre,
                edad = excluded.edad,
                sexo = excluded.sexo,
                peso = excluded.peso,
                altura = excluded.altura,
                activity_level = excluded.activity_level,
                objetivo = excluded.objetivo,
                dietary_restrictions = excluded.dietary_restrictions,
                food_preferences = excluded.food_preferences,
                budget = excluded.budget,
                ultima_actualizacion = CURRENT_TIMESTAMP
            """,
            (
                user.whatsapp_number,
                user.name,
                user.age,
                user.sex,
                user.weight,
                user.height,
                user.activity_level,
                user.goal,
                json.dumps(user.dietary_restrictions),
                json.dumps(user.food_preferences),
                user.budget,
            ),
        )

        conn.commit()
        conn.close()

    def get_by_whatsapp(self, whatsapp_number: str) -> Optional[UserProfile]:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE whatsapp_number = ?
            """,
            (whatsapp_number,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return UserProfile(
            id=row["usuario_id"],
            whatsapp_number=row["whatsapp_number"],
            name=row["nombre"],
            age=row["edad"],
            sex=row["sexo"],
            weight=row["peso"],
            height=row["altura"],
            activity_level=row["activity_level"],
            goal=row["objetivo"],
            dietary_restrictions=json.loads(row["dietary_restrictions"] or "[]"),
            food_preferences=json.loads(row["food_preferences"] or "[]"),
            budget=row["budget"],
        )

    def update(self, user: UserProfile):
        self.create(user)

    def delete(self, whatsapp_number: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM users
            WHERE whatsapp_number = ?
            """,
            (whatsapp_number,),
        )
        conn.commit()
        conn.close()

    def exists(self, whatsapp_number: str) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 1
            FROM users
            WHERE whatsapp_number = ?
            LIMIT 1
            """,
            (whatsapp_number,),
        )
        result = cursor.fetchone()
        conn.close()
        return result is not None
