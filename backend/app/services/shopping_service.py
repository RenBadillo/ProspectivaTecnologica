from app.models.shopping_item import ShoppingItem
from app.models.shopping_list import ShoppingList


class ShoppingService:

    PROTEINS = {
        "pollo",
        "atun",
        "atún",
        "huevo",
        "huevos",
        "carne",
        "pescado",
        "salmon",
        "salmón",
        "yogurt griego",
        "queso cottage",
        "frijoles",
        "lentejas"
    }

    VEGETABLES = {
        "brocoli",
        "brócoli",
        "zanahoria",
        "espinaca",
        "lechuga",
        "pepino",
        "jitomate",
        "tomate",
        "calabaza"
    }

    FRUITS = {
        "manzana",
        "platano",
        "plátano",
        "pera",
        "naranja",
        "fresas",
        "uva"
    }

    CARBS = {
        "arroz",
        "pasta",
        "avena",
        "tortilla",
        "pan",
        "papa",
        "camote"
    }

    def generate_shopping_list(
        self,
        inventory: list[dict]
    ) -> ShoppingList:

        items = []

        inventory_names = {
            item["name"].lower()
            for item in inventory
        }

        # PROTEÍNAS

        has_protein = any(
            food in inventory_names
            for food in self.PROTEINS
        )

        if not has_protein:

            items.append(
                ShoppingItem(
                    name="pollo",
                    quantity=1,
                    unit="kg",
                    priority="HIGH",
                    reason="No se detectaron proteínas principales"
                )
            )

        # VERDURAS

        has_vegetables = any(
            food in inventory_names
            for food in self.VEGETABLES
        )

        if not has_vegetables:

            items.append(
                ShoppingItem(
                    name="brócoli",
                    quantity=1,
                    unit="pieza",
                    priority="MEDIUM",
                    reason="No se detectaron verduras"
                )
            )

        # FRUTAS

        has_fruits = any(
            food in inventory_names
            for food in self.FRUITS
        )

        if not has_fruits:

            items.append(
                ShoppingItem(
                    name="manzana",
                    quantity=4,
                    unit="pieza",
                    priority="LOW",
                    reason="No se detectaron frutas"
                )
            )

        # CARBOHIDRATOS

        has_carbs = any(
            food in inventory_names
            for food in self.CARBS
        )

        if not has_carbs:

            items.append(
                ShoppingItem(
                    name="arroz",
                    quantity=1,
                    unit="kg",
                    priority="MEDIUM",
                    reason="No se detectaron carbohidratos base"
                )
            )

        return ShoppingList(
            items=items
        )