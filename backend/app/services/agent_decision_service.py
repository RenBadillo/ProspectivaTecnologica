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
        low_stock_items = inventory_state["low_stock_items"]

        messages = []

        if urgent_items:
            messages.append(
                "Detecté productos que conviene consumir pronto:"
            )

            for item in urgent_items:
                messages.append(
                    f"- {item['name']} lleva "
                    f"{item['days_in_inventory']} días en inventario. "
                    f"Como es {item['category']}, su vida útil sugerida "
                    f"es de {item['threshold_days']} días."
                )

        if soon_items:
            messages.append(
                "También hay productos próximos a llegar a su límite sugerido:"
            )

            for item in soon_items:
                messages.append(
                    f"- {item['name']} tiene aproximadamente "
                    f"{item['days_left']} días restantes de vida útil sugerida."
                )

        if low_stock_items:
            messages.append(
                "Además, detecté productos con stock bajo:"
            )

            for item in low_stock_items:
                messages.append(
                    f"- {item['name']} tiene cantidad {item['quantity']}."
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
        available_items = inventory_state["available_items"]

        priority_names = [
            item["name"]
            for item in urgent_items
        ] + [
            item["name"]
            for item in soon_items
        ]

        all_items_text = "\n".join([
            (
                f"- {item['name']} "
                f"(cantidad: {item['quantity']}, "
                f"categoría: {item['category']}, "
                f"días en inventario: {item['days_in_inventory']}, "
                f"vida útil sugerida: {item['threshold_days']})"
            )
            for item in available_items
        ])

        priority_text = (
            "\n".join([f"- {name}" for name in priority_names])
            if priority_names
            else "No hay ingredientes urgentes."
        )

        return (
            "ESTADO COMPLETO DEL INVENTARIO:\n"
            f"{all_items_text}\n\n"
            "INGREDIENTES PRIORITARIOS PARA EVITAR DESPERDICIO:\n"
            f"{priority_text}\n\n"
            "INSTRUCCIÓN DE AGENTE:\n"
            "Si el usuario pide receta o plan de comida, prioriza los "
            "ingredientes urgentes o próximos a caducar, pero considera "
            "todo el inventario disponible para crear una recomendación "
            "más completa y útil."
        )