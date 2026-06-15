class InventoryFormatter:

    @staticmethod
    def to_prompt(inventory: list[dict]) -> str:

        if not inventory:
            return "Inventario vacío."

        return "\n".join(
            f"- {item['name']} (cantidad: {item['quantity']})"
            for item in inventory
            if item.get("quantity", 0) > 0
        )

    @staticmethod
    def get_available_names(inventory: list[dict]) -> list[str]:

        return [
            item["name"].lower().strip()
            for item in inventory
            if item.get("quantity", 0) > 0
        ]