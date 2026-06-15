from app.data.food_catalog import (
    PROTEINS,
    VEGETABLES,
    FRUITS,
    CARBS,
)

class InventoryAnalysisService:

    LOW_STOCK_THRESHOLD = 2

    def analyze_inventory(
        self,
        inventory: list[dict]
    ) -> dict:

        missing = []
        low_stock = []
        duplicates = []
        recommendations = []

        names_seen = set()

        for item in inventory:

            name = item["name"].lower()
            quantity = item["quantity"]

            if quantity <= 0:
                missing.append(name)

            elif quantity <= self.LOW_STOCK_THRESHOLD:
                low_stock.append(name)

            if name in names_seen:
                duplicates.append(name)

            names_seen.add(name)

        inventory_names = {
            item["name"].lower()
            for item in inventory
            if item["quantity"] > 0
        }

        if not any(x in inventory_names for x in PROTEINS):
            recommendations.append(
                "Agregar una fuente principal de proteína."
            )

        if not any(x in inventory_names for x in VEGETABLES):
            recommendations.append(
                "Agregar verduras para mejorar micronutrientes."
            )

        if not any(x in inventory_names for x in FRUITS):
            recommendations.append(
                "Agregar frutas para aumentar fibra y vitaminas."
            )

        if not any(x in inventory_names for x in CARBS):
            recommendations.append(
                "Agregar una fuente de carbohidratos complejos."
            )

        return {
            "missing": missing,
            "low_stock": low_stock,
            "duplicates": duplicates,
            "recommendations": recommendations
        }