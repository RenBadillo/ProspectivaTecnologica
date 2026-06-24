from app.services.agent_decision_service import AgentDecisionService
from app.models.user_profile import UserProfile
from app.database.user_repository import UserRepository
from app.services.inventory_service import InventoryService
from app.services.inventory_analysis_service import InventoryAnalysisService
from app.services.llm_service import LLMService
from app.services.meal_plan_service import MealPlanService
from app.services.nutrition_service import NutritionService
from app.services.recipe_service import RecipeService
from app.services.shopping_service import ShoppingService


class ChatRouterService:

    registration_sessions = {}

    def __init__(self):
        self.inventory_service = InventoryService()
        self.inventory_analysis_service = InventoryAnalysisService()
        self.recipe_service = RecipeService()
        self.shopping_service = ShoppingService()
        self.meal_plan_service = MealPlanService()
        self.nutrition_service = NutritionService()
        self.user_repository = UserRepository()
        self.llm_service = LLMService()
        self.agent_decision_service = AgentDecisionService()

    def classify(self, message: str) -> str:
        text = message.lower().strip()

        if text.startswith("registrar perfil"):
            return "register_profile"

        if any(p in text for p in [
            "cambia", "cambiar", "renombra", "renombrar",
            "corrige", "corregir"
        ]):
            return "rename_inventory"

        if any(p in text for p in [
            "recordatorio", "recordatorios",
            "caducidad", "caducar",
            "consumir pronto",
            "qué se va a echar a perder",
            "que se va a echar a perder"
        ]):
            return "reminders"

        if any(p in text for p in [
            "agrega", "agregar", "puedes agregar",
            "añade", "añadir", "compré", "compre",
            "sumar al inventario"
        ]):
            return "add_inventory"

        if any(p in text for p in [
            "elimina", "eliminar", "quita", "quitar",
            "consumí", "consumi", "usé", "use",
            "gasté", "gaste"
        ]):
            return "remove_inventory"

        if any(p in text for p in [
            "inventario", "qué tengo", "que tengo",
            "qué hay", "que hay", "mis productos",
            "alacena"
        ]):
            return "inventory"

        if any(p in text for p in [
            "analiza inventario", "analiza mi despensa",
            "estado de mi despensa", "revisa mi inventario"
        ]):
            return "inventory_analysis"

        if any(p in text for p in [
            "receta", "cocinar", "qué puedo cocinar",
            "que puedo cocinar", "qué como", "que como",
            "qué preparo", "que preparo"
        ]):
            return "recipe"

        if any(p in text for p in [
            "compras", "lista de compras", "qué falta",
            "que falta", "qué me falta", "que me falta",
            "qué necesito comprar", "que necesito comprar"
        ]):
            return "shopping"

        if any(p in text for p in [
            "dieta", "plan semanal", "meal plan",
            "plan alimenticio", "plan de comida"
        ]):
            return "meal_plan"

        if any(p in text for p in [
            "calorías", "calorias", "macros",
            "proteína", "proteina", "tmb", "get"
        ]):
            return "nutrition"

        return "general"

    async def handle_message(
        self,
        whatsapp_number: str,
        message: str
    ) -> str:

        if whatsapp_number in self.registration_sessions:
            return self.continue_registration(
                whatsapp_number,
                message
            )

        user = self.user_repository.get_by_whatsapp(
            whatsapp_number
        )

        if not user and not message.lower().startswith("registrar perfil"):
            self.start_registration(whatsapp_number)
            return (
                "Hola. No encontré tu perfil nutricional.\n\n"
                "Vamos a registrarlo paso a paso.\n"
                "Primero, ¿cómo te llamas?"
            )

        intent = self.classify(message)

        inventory = self.inventory_service.load_inventory_from_db()

        inventory_state = (
            self.agent_decision_service
            .analyze_inventory_state(inventory)
        )

        agent_message = (
            self.agent_decision_service
            .build_agent_message(inventory_state)
        )

        if intent == "register_profile":
            return self.handle_register_profile(
                whatsapp_number,
                message
            )

        if intent == "rename_inventory":
            return self.handle_rename_inventory(message)

        if intent == "reminders":
            return self.handle_reminders()

        if intent == "add_inventory":
            return self.handle_add_inventory(message)

        if intent == "remove_inventory":
            return self.handle_remove_inventory(message)

        if intent == "inventory":
            return self.handle_inventory()

        if intent == "inventory_analysis":
            return self.handle_inventory_analysis()

        if intent == "recipe":
            agent_context = (
                self.agent_decision_service
                .build_recipe_priority_context(
                    inventory_state
                )
            )

            recipe = await self.recipe_service.generate_recipe(
                whatsapp_number,
                agent_context=agent_context
            )

            return self.add_agent_notice(
                "Recomendación del agente:\n" + recipe,
                agent_message
            )

        if intent == "shopping":
            shopping_response = self.handle_shopping()

            return self.add_agent_notice(
                shopping_response,
                agent_message
            )

        if intent == "nutrition":
            return self.handle_nutrition(
                whatsapp_number
            )

        if intent == "meal_plan":
            meal_plan = self.handle_meal_plan(
                whatsapp_number
            )

            return self.add_agent_notice(
                meal_plan,
                agent_message
            )

        return await self.handle_general(
            message,
            agent_message=agent_message
        )

    def start_registration(
        self,
        whatsapp_number: str
    ):

        self.registration_sessions[whatsapp_number] = {
            "step": "name",
            "data": {}
        }

    def continue_registration(
        self,
        whatsapp_number: str,
        message: str
    ) -> str:

        session = self.registration_sessions[
            whatsapp_number
        ]

        step = session["step"]
        data = session["data"]
        text = message.strip()

        try:
            if step == "name":
                data["name"] = text
                session["step"] = "age"
                return "Gracias. ¿Cuántos años tienes?"

            if step == "age":
                data["age"] = int(text)
                session["step"] = "sex"
                return (
                    "¿Cuál es tu sexo biológico para el cálculo nutricional?\n"
                    "Responde: female o male"
                )

            if step == "sex":
                text = text.lower()

                if text not in ["female", "male"]:
                    return "Responde únicamente: female o male"

                data["sex"] = text
                session["step"] = "weight"
                return "¿Cuánto pesas en kg? Ejemplo: 60"

            if step == "weight":
                data["weight"] = float(text)
                session["step"] = "height"
                return "¿Cuánto mides en metros? Ejemplo: 1.65"

            if step == "height":
                data["height"] = float(text)
                session["step"] = "activity"
                return (
                    "¿Cuál es tu nivel de actividad?\n\n"
                    "Opciones:\n"
                    "- sedentary\n"
                    "- light\n"
                    "- moderate\n"
                    "- active\n"
                    "- very_active"
                )

            if step == "activity":
                text = text.lower()

                valid = [
                    "sedentary",
                    "light",
                    "moderate",
                    "active",
                    "very_active"
                ]

                if text not in valid:
                    return (
                        "Actividad no válida.\n"
                        "Usa: sedentary, light, moderate, active o very_active"
                    )

                data["activity_level"] = text
                session["step"] = "goal"
                return (
                    "¿Cuál es tu objetivo?\n\n"
                    "Opciones:\n"
                    "- weight_loss\n"
                    "- muscle_gain\n"
                    "- maintenance\n"
                    "- recomposition"
                )

            if step == "goal":
                text = text.lower()

                valid = [
                    "weight_loss",
                    "muscle_gain",
                    "maintenance",
                    "recomposition"
                ]

                if text not in valid:
                    return (
                        "Objetivo no válido.\n"
                        "Usa: weight_loss, muscle_gain, maintenance o recomposition"
                    )

                data["goal"] = text

                user = UserProfile(
                    id=None,
                    whatsapp_number=whatsapp_number,
                    name=data["name"],
                    age=data["age"],
                    sex=data["sex"],
                    weight=data["weight"],
                    height=data["height"],
                    activity_level=data["activity_level"],
                    goal=data["goal"],
                    dietary_restrictions=[],
                    food_preferences=[],
                    budget=None
                )

                self.user_repository.create(user)

                del self.registration_sessions[
                    whatsapp_number
                ]

                return (
                    "Perfil registrado correctamente.\n\n"
                    f"Nombre: {user.name}\n"
                    f"Edad: {user.age}\n"
                    f"Sexo: {user.sex}\n"
                    f"Peso: {user.weight} kg\n"
                    f"Altura: {user.height} m\n"
                    f"Actividad: {user.activity_level}\n"
                    f"Objetivo: {user.goal}\n\n"
                    "Ya puedes pedirme recetas, compras, inventario o plan semanal."
                )

        except ValueError:
            return (
                "No pude entender ese dato. "
                "Revisa el formato e inténtalo otra vez."
            )

        return "Ocurrió un error durante el registro."

    def add_agent_notice(
        self,
        response: str,
        agent_message: str
    ) -> str:

        if not agent_message:
            return response

        return (
            "Aviso del agente:\n"
            + agent_message
            + "\n\n"
            + response
        )

    def handle_inventory(self) -> str:
        inventory = self.inventory_service.load_inventory_from_db()

        if not inventory:
            return (
                "Tu inventario está vacío. "
                "Agrega productos primero."
            )

        lines = []

        for item in inventory:
            lines.append(
                f"- {item['name']} "
                f"(cantidad: {item['quantity']})"
            )

        return (
            "Inventario actual:\n"
            + "\n".join(lines)
        )

    def handle_reminders(self) -> str:
        reminders = (
            self.inventory_service
            .get_consumption_reminders()
        )

        if not reminders:
            return (
                "No detecté productos que necesiten "
                "recordatorio de consumo por ahora."
            )

        lines = []

        for reminder in reminders:
            lines.append(
                f"- {reminder['name']} "
                f"({reminder['days_in_inventory']} días, "
                f"{reminder['category_label']})"
            )

        return (
            "Productos que conviene consumir pronto:\n"
            + "\n".join(lines)
        )

    def handle_rename_inventory(self, message: str) -> str:
        text = message.lower().strip()

        patterns = [
            ("cambia", "por"),
            ("cambiar", "por"),
            ("renombra", "como"),
            ("renombrar", "como"),
            ("corrige", "por"),
            ("corregir", "por")
        ]

        old_name = None
        new_name = None

        for start_word, separator in patterns:
            if start_word in text and separator in text:
                clean_text = (
                    text.replace(start_word, "", 1)
                    .replace("el producto", "")
                    .replace("producto", "")
                    .strip()
                )

                parts = clean_text.split(separator, 1)

                if len(parts) == 2:
                    old_name = parts[0].strip()
                    new_name = parts[1].strip()
                    break

        if not old_name or not new_name:
            return (
                "No pude identificar qué producto quieres cambiar.\n\n"
                "Usa este formato:\n"
                "cambia cooper por cereal\n\n"
                "o:\n"
                "renombra cooper como cereal"
            )

        success = self.inventory_service.rename_food(
            old_name=old_name,
            new_name=new_name
        )

        if not success:
            return (
                f"No encontré '{old_name}' en el inventario. "
                "Revisa el nombre exacto e inténtalo de nuevo."
            )

        return (
            "Producto actualizado correctamente:\n"
            f"- {old_name} → {new_name}"
        )

    def handle_add_inventory(self, message: str) -> str:
        lines = message.lower().splitlines()
        added_items = []

        for line in lines:
            line = line.strip()

            if not line:
                continue

            line = (
                line.replace("puedes agregar:", "")
                .replace("puedes agregar", "")
                .replace("agrega:", "")
                .replace("agrega", "")
                .replace("añade:", "")
                .replace("añade", "")
                .strip()
            )

            parts = line.split()

            if len(parts) < 2:
                continue

            try:
                quantity = int(parts[0])
                name = " ".join(parts[1:]).strip()
            except ValueError:
                continue

            if name:
                self.inventory_service.add_food(
                    name=name,
                    quantity=quantity,
                    source="whatsapp"
                )

                added_items.append(
                    f"- {name} (cantidad: {quantity})"
                )

        if not added_items:
            return (
                "No pude identificar productos para agregar.\n\n"
                "Usa este formato:\n"
                "agrega:\n"
                "2 lata de atún\n"
                "1 paquete de arroz"
            )

        return (
            "Productos agregados al inventario:\n"
            + "\n".join(added_items)
        )

    def handle_remove_inventory(self, message: str) -> str:
        lines = message.lower().splitlines()
        removed_items = []
        failed_items = []

        for line in lines:
            line = line.strip()

            if not line:
                continue

            line = (
                line.replace("elimina:", "")
                .replace("elimina", "")
                .replace("eliminar:", "")
                .replace("eliminar", "")
                .replace("quita:", "")
                .replace("quita", "")
                .replace("quitar:", "")
                .replace("quitar", "")
                .replace("consumí:", "")
                .replace("consumí", "")
                .replace("consumi:", "")
                .replace("consumi", "")
                .replace("usé:", "")
                .replace("usé", "")
                .replace("use:", "")
                .replace("use", "")
                .replace("gasté:", "")
                .replace("gasté", "")
                .replace("gaste:", "")
                .replace("gaste", "")
                .strip()
            )

            parts = line.split()

            if len(parts) < 2:
                continue

            try:
                quantity = int(parts[0])
                name = " ".join(parts[1:]).strip()
            except ValueError:
                continue

            success = self.inventory_service.remove_food(
                name=name,
                quantity=quantity
            )

            if success:
                removed_items.append(
                    f"- {name} (cantidad: {quantity})"
                )
            else:
                failed_items.append(
                    f"- {name} (cantidad: {quantity})"
                )

        if not removed_items and not failed_items:
            return (
                "No pude identificar productos para eliminar.\n\n"
                "Usa este formato:\n"
                "elimina:\n"
                "1 huevo\n"
                "2 zanahoria"
            )

        response = ""

        if removed_items:
            response += (
                "Productos descontados del inventario:\n"
                + "\n".join(removed_items)
            )

        if failed_items:
            if response:
                response += "\n\n"

            response += (
                "No pude descontar estos productos "
                "porque no existen o no hay suficiente cantidad:\n"
                + "\n".join(failed_items)
            )

        return response

    def handle_inventory_analysis(self) -> str:
        inventory = self.inventory_service.load_inventory_from_db()

        if not inventory:
            return (
                "Tu inventario está vacío. "
                "No hay productos para analizar."
            )

        analysis = self.inventory_analysis_service.analyze_inventory(
            inventory
        )

        response = "Análisis de inventario:\n\n"

        if analysis["missing"]:
            response += (
                "Productos agotados:\n"
                + "\n".join(f"- {p}" for p in analysis["missing"])
                + "\n\n"
            )

        if analysis["low_stock"]:
            response += (
                "Stock bajo:\n"
                + "\n".join(f"- {p}" for p in analysis["low_stock"])
                + "\n\n"
            )

        if analysis["duplicates"]:
            response += (
                "Productos duplicados:\n"
                + "\n".join(f"- {p}" for p in analysis["duplicates"])
                + "\n\n"
            )

        if analysis["recommendations"]:
            response += (
                "Recomendaciones:\n"
                + "\n".join(
                    f"- {r}" for r in analysis["recommendations"]
                )
            )

        return response.strip()

    def handle_shopping(self) -> str:
        inventory = self.inventory_service.load_inventory_from_db()

        shopping_list = self.shopping_service.generate_shopping_list(
            inventory
        )

        if not shopping_list.items:
            return (
                "Tu inventario se ve balanceado por ahora. "
                "No detecté compras críticas."
            )

        lines = [
            (
                f"- {item.name} "
                f"({item.quantity} {item.unit}) "
                f"[{item.priority}]: {item.reason}"
            )
            for item in shopping_list.items
        ]

        return "Lista de compras sugerida:\n" + "\n".join(lines)

    def handle_nutrition(
        self,
        whatsapp_number: str
    ) -> str:

        user = self.user_repository.get_by_whatsapp(
            whatsapp_number
        )

        if not user:
            return (
                "No encontré tu perfil nutricional.\n\n"
                "Escribe cualquier mensaje y te registraré paso a paso."
            )

        profile = self.nutrition_service.generate_profile(
            user
        )

        return (
            "Perfil nutricional calculado:\n"
            f"TMB: {profile.tmb} kcal\n"
            f"GET: {profile.get} kcal\n"
            f"Calorías objetivo: {profile.calories_target} kcal\n"
            f"Proteínas: {profile.protein_target} g\n"
            f"Carbohidratos: {profile.carb_target} g\n"
            f"Grasas: {profile.fat_target} g"
        )

    def handle_meal_plan(
        self,
        whatsapp_number: str
    ) -> str:

        user = self.user_repository.get_by_whatsapp(
            whatsapp_number
        )

        if not user:
            return (
                "No encontré tu perfil nutricional.\n\n"
                "Escribe cualquier mensaje y te registraré paso a paso."
            )

        profile = self.nutrition_service.generate_profile(
            user
        )

        inventory = self.inventory_service.load_inventory_from_db()

        plan_text = self.meal_plan_service.generate_text_meal_plan(
            nutrition_profile=profile,
            inventory=inventory,
            goal=user.goal
        )

        return plan_text

    async def handle_general(
        self,
        message: str,
        agent_message: str = ""
    ) -> str:

        inventory = self.inventory_service.load_inventory_from_db()

        inventory_text = (
            ", ".join(
                f"{item['name']} x{item['quantity']}"
                for item in inventory
            )
            if inventory
            else "inventario vacío"
        )

        response = await self.llm_service.generate(
            prompt=(
                "Eres un asistente de alacena inteligente. "
                "Responde en español, claro y breve.\n"
                f"Inventario completo: {inventory_text}\n"
                f"Observaciones del agente: {agent_message or 'sin alertas'}\n"
                f"Usuario: {message}"
            ),
            temperature=0.4,
            max_tokens=180
        )

        return response.content

    def handle_register_profile(
        self,
        whatsapp_number: str,
        message: str
    ) -> str:

        try:
            data_text = message.replace(
                "registrar perfil:",
                ""
            ).replace(
                "registrar perfil",
                ""
            ).strip()

            data = {}

            parts = data_text.split(",")

            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    data[key.strip().lower()] = value.strip()

            required_fields = [
                "edad",
                "peso",
                "altura"
            ]

            for field in required_fields:
                if field not in data:
                    return (
                        "Faltan datos para registrar el perfil.\n\n"
                        "Usa este formato:\n"
                        "registrar perfil: nombre=Renata, edad=22, sexo=female, "
                        "peso=60, altura=1.65, actividad=moderate, objetivo=muscle_gain"
                    )

            user = UserProfile(
                id=None,
                whatsapp_number=whatsapp_number,
                name=data.get("nombre", "Usuario"),
                age=int(data.get("edad")),
                sex=data.get("sexo", "female"),
                weight=float(data.get("peso")),
                height=float(data.get("altura")),
                activity_level=data.get("actividad", "moderate"),
                goal=data.get("objetivo", "maintenance"),
                dietary_restrictions=[],
                food_preferences=[],
                budget=None
            )

            self.user_repository.create(user)

            return (
                "Perfil registrado correctamente.\n\n"
                f"Nombre: {user.name}\n"
                f"Edad: {user.age}\n"
                f"Peso: {user.weight} kg\n"
                f"Altura: {user.height} m\n"
                f"Actividad: {user.activity_level}\n"
                f"Objetivo: {user.goal}\n\n"
                "Ya puedes pedirme recetas, compras o tu plan semanal."
            )

        except Exception:
            return (
                "No pude registrar el perfil.\n\n"
                "Usa este formato:\n"
                "registrar perfil: nombre=Renata, edad=22, sexo=female, "
                "peso=60, altura=1.65, actividad=moderate, objetivo=muscle_gain"
            )