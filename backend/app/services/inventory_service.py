import json
from pathlib import Path
from datetime import datetime

from app.database.connection import get_connection


class InventoryService:

    PERISHABLE_RULES = {
        "cooked_food": {
            "keywords": [
                "cocido",
                "cocida",
                "guisado",
                "sopa",
                "caldo",
                "arroz cocido",
                "pasta cocida",
                "pollo cocido",
                "sobras",
                "comida preparada"
            ],
            "threshold_days": 3,
            "label": "sobras o comida preparada"
        },
        "fruit": {
            "keywords": [
                "manzana",
                "plátano",
                "platano",
                "pera",
                "naranja",
                "fresa",
                "uvas",
                "uva",
                "mango",
                "piña",
                "pina",
                "sandía",
                "sandia",
                "melón",
                "melon",
                "kiwi",
                "papaya",
                "durazno",
                "limón",
                "limon",
                "aguacate"
            ],
            "threshold_days": 5,
            "label": "fruta"
        },
        "vegetable": {
            "keywords": [
                "zanahoria",
                "lechuga",
                "espinaca",
                "brócoli",
                "brocoli",
                "jitomate",
                "tomate",
                "pepino",
                "calabaza",
                "cebolla",
                "papa",
                "chile",
                "apio",
                "cilantro"
            ],
            "threshold_days": 5,
            "label": "verdura"
        }
    }

    def load_inventory(self):
        path = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "inventario.json"
        )

        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def add_food(
        self,
        name,
        quantity,
        source
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO inventory(
                name,
                quantity,
                source,
                added_at,
                last_update
            )
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)

            ON CONFLICT(name)
            DO UPDATE SET
                quantity = inventory.quantity + excluded.quantity,
                source = excluded.source,
                last_update = CURRENT_TIMESTAMP
            """,
            (
                name.lower().strip(),
                quantity,
                source
            )
        )

        conn.commit()
        conn.close()

    def remove_food(
        self,
        name,
        quantity
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE inventory
            SET
                quantity = quantity - ?,
                last_update = CURRENT_TIMESTAMP
            WHERE name = ?
            AND quantity >= ?
            """,
            (
                quantity,
                name.lower().strip(),
                quantity
            )
        )

        conn.commit()
        updated_rows = cursor.rowcount
        conn.close()

        return updated_rows > 0

    def rename_food(
        self,
        old_name: str,
        new_name: str
    ) -> bool:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE inventory
            SET
                name = ?,
                last_update = CURRENT_TIMESTAMP
            WHERE name = ?
            """,
            (
                new_name.lower().strip(),
                old_name.lower().strip()
            )
        )

        conn.commit()
        updated_rows = cursor.rowcount
        conn.close()

        return updated_rows > 0

    def load_inventory_from_db(self):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                name,
                quantity,
                source,
                last_update,
                COALESCE(added_at, last_update) AS added_at
            FROM inventory
            ORDER BY name ASC
            """
        )

        rows = cursor.fetchall()
        conn.close()

        inventory = []

        for row in rows:
            item = dict(row)

            category_data = self.detect_perishable_category(
                item["name"]
            )

            item["category"] = category_data["category"]
            item["category_label"] = category_data["label"]
            item["threshold_days"] = category_data["threshold_days"]

            item["days_in_inventory"] = (
                self.calculate_days_in_inventory(
                    item.get("added_at")
                )
            )

            item["should_remind"] = (
                item["quantity"] > 0
                and item["threshold_days"] is not None
                and item["days_in_inventory"] >= item["threshold_days"]
            )

            inventory.append(item)

        return inventory

    def detect_perishable_category(
        self,
        name: str
    ) -> dict:

        clean_name = name.lower().strip()

        for category, rule in self.PERISHABLE_RULES.items():
            for keyword in rule["keywords"]:
                if keyword in clean_name:
                    return {
                        "category": category,
                        "label": rule["label"],
                        "threshold_days": rule["threshold_days"]
                    }

        return {
            "category": "unknown",
            "label": "sin categoría",
            "threshold_days": None
        }

    def calculate_days_in_inventory(
        self,
        added_at
    ) -> int:

        if not added_at:
            return 0

        try:
            added_date = datetime.fromisoformat(
                str(added_at).replace("Z", "")
            )

            now = datetime.now()

            return max(
                0,
                (now - added_date).days
            )

        except Exception:
            return 0

    def get_consumption_reminders(self):

        inventory = self.load_inventory_from_db()

        reminders = []

        for item in inventory:

            if item["quantity"] <= 0:
                continue

            if not item["should_remind"]:
                continue

            reminders.append({
                "name": item["name"],
                "quantity": item["quantity"],
                "category": item["category"],
                "category_label": item["category_label"],
                "days_in_inventory": item["days_in_inventory"],
                "threshold_days": item["threshold_days"],
                "message": (
                    f"{item['name']} lleva "
                    f"{item['days_in_inventory']} días en inventario. "
                    f"Como es {item['category_label']}, "
                    "conviene consumirlo pronto para evitar desperdicio."
                )
            })

        return reminders