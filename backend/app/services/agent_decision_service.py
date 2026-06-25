class AgentDecisionService:

    def analyze_inventory_state(
        self,
        inventory: list[dict]
    ) -> dict:

        urgent_items = []
        soon_items = []
        low_stock_items = []
        available_items = []

        for item in inventory:
            name = item.get("name", "")
            quantity = item.get("quantity", 0)
            days = item.get("days_in_inventory", 0)
            threshold = item.get("threshold_days")
            category = item.get(
                "category_label",
                "sin categoría"
            )

            if quantity <= 0:
                continue

            available_items.append({
                "name": name,
                "quantity": quantity,
                "category": category,
                "days_in_inventory": days,
                "threshold_days": threshold
            })

            if quantity <= 2:
                low_stock_items.append({
                    "name": name,
                    "quantity": quantity,
                    "reason": "stock bajo"
                })

            if threshold is not None:
                days_left = threshold - days

                if days_left <= 0:
                    urgent_items.append({
                        "name": name,
                        "quantity": quantity,
                        "category": category,
                        "days_in_inventory": days,
                        "threshold_days": threshold,
                        "reason": (
                            "ya alcanzó o superó su vida útil sugerida"
                        )
                    })

                elif days_left <= 2:
                    soon_items.append({
                        "name": name,
                        "quantity": quantity,
                        "category": category,
                        "days_in_inventory": days,
                        "threshold_days": threshold,
                        "days_left": days_left,
                        "reason": (
                            "está próximo a alcanzar su vida útil sugerida"
                        )
                    })

        return {
            "available_items": available_items,
            "urgent_items": urgent_items,
            "soon_items": soon_items,
            "low_stock_items": low_stock_items
        }

    def build_agent_message(
        self,
        inventory_state: dict
    ) -> str:

        urgent_items = inventory_state["urgent_items"]
        soon_items = inventory_state["soon_items"]

        messages = []

        if urgent_items:
            messages.append(
                "Detecté productos que conviene consumir pronto:"
            )

            for item in urgent_items:
                messages.append(
                    f"- {item['name']} lleva "
                    f"{item['days_in_inventory']} días en inventario."
                )

        if soon_items:
            messages.append(
                "También hay productos próximos a consumirse preferentemente:"
            )

            for item in soon_items:
                messages.append(
                    f"- {item['name']} tiene aproximadamente "
                    f"{item['days_left']} días restantes."
                )

        if not messages:
            return ""

        return "\n".join(messages)

    def build_recipe_priority_context(
        self,
        inventory_state: dict
    ) -> str:

        urgent_items = inventory_state["urgent_items"]
        soon_items = inventory_state["soon_items"]

        total_priority = (
            len(urgent_items)
            + len(soon_items)
        )
        
        if total_priority == 0:
            return(
                "No existen ingredientes prioritarios"
                "por antigüedad"
            )

        return (
            f"Existen {total_priority} ingredientes "
            "prioritarios por antigüedad"
            "Priorízalos cuando sea razonable, "
            "pero considera todo el Inventario."
        )

        if not priority_items:
            return (
                "No hay ingredientes prioritarios por antigüedad. "
                "Genera la receta considerando el inventario disponible."
            )

        priority_text = "\n".join([
            (
                f"- {item['name']} "
                f"(cantidad: {item['quantity']}, "
                f"{item['days_in_inventory']} días en inventario, "
                f"{item['category']})"
            )
            for item in priority_items
        ])

        return (
            "INGREDIENTES PRIORITARIOS INTERNOS:\n"
            f"{priority_text}\n\n"
            "Usa estos ingredientes preferentemente si tiene sentido, "
            "pero no menciones alertas de caducidad a menos que el usuario lo pida."
        )