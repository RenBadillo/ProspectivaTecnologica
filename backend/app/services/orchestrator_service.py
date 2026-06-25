import json
import re

from app.services.llm_service import LLMService


class OrchestratorService:

    VALID_INTENTS = [
        "inventory",
        "add_inventory",
        "remove_inventory",
        "rename_inventory",
        "recipe",
        "shopping",
        "meal_plan",
        "nutrition",
        "reminders",
        "profile_register",
        "general"
    ]

    def __init__(self):
        self.llm_service = LLMService()

    async def decide(self, message: str) -> dict:

        prompt = f"""
Eres un agente orquestador para una alacena inteligente.

Tu tarea es interpretar lenguaje natural y devolver SOLO un JSON válido.

No respondas al usuario final.
No uses markdown.
No agregues texto fuera del JSON.

INTENTS PERMITIDOS:
inventory, add_inventory, remove_inventory, rename_inventory, recipe, shopping, meal_plan, nutrition, reminders, profile_register, general.

ESQUEMA OBLIGATORIO:
{{
  "intent": "add_inventory",
  "action": "add_food",
  "confidence": 0.95,
  "entities": {{
    "items": [
      {{
        "name": "mangos",
        "quantity": 2
      }}
    ],
    "old_name": null,
    "new_name": null
  }},
  "needs_profile": false,
  "reason": "El usuario indica que compró productos para agregarlos al inventario."
}}

REGLAS DE INTENT:
- Si pregunta qué tiene, qué productos hay, qué comida queda, qué hay en la alacena o despensa: inventory.
- Si dice compré, compre, agregué, agregue, mete, añade, registra, sumé, llegó, tengo ahora: add_inventory.
- Si dice quita, elimina, borra, me comí, consumí, usé, gasté, ya no tengo: remove_inventory.
- Si dice cambia, corrige, renombra, era, quise decir, sustituye nombre: rename_inventory.
- Si pide receta, comida o qué cocinar: recipe.
- Si pide lista de compras, súper o qué comprar: shopping.
- Si pide plan semanal, dieta o plan alimenticio: meal_plan.
- Si pide calorías, macros, TMB o GET: nutrition.
- Si pregunta qué consumir pronto o qué se puede echar a perder: reminders.
- Si quiere registrar datos personales: profile_register.
- Si no queda claro: general.

REGLAS DE ENTIDADES:
- Para add_inventory y remove_inventory extrae entities.items.
- Cada item debe tener:
  - name: nombre del producto en plural o nombre natural.
  - quantity: número entero.
- Convierte cantidades escritas con palabras:
  - "un", "una" = 1
  - "dos" = 2
  - "tres" = 3
  - "cuatro" = 4
  - "cinco" = 5
  - "seis" = 6
  - "siete" = 7
  - "ocho" = 8
  - "nueve" = 9
  - "diez" = 10
- Si el usuario dice "Compré dos mangos", devuelve:
  "items": [{{"name": "mangos", "quantity": 2}}]
- Si dice "Compré una leche y dos huevos", devuelve dos items.
- Si no hay cantidad explícita, usa quantity = 1.

REGLAS PARA RENOMBRAR:
- Para rename_inventory usa:
  "old_name": nombre anterior
  "new_name": nombre corregido
- Ejemplo: "cambia cooper por cereal"
  old_name = "cooper"
  new_name = "cereal"

MENSAJE DEL USUARIO:
{message}
"""

        response = await self.llm_service.generate(
            prompt=prompt,
            temperature=0.0,
            max_tokens=260,
            format_json=True
        )

        if not response.success:
            return self.fallback_decision(
                message=message,
                raw_response=response.content,
                json_valid=False,
                schema_valid=False,
                model=response.model,
                tokens_used=response.tokens_used
            )

        raw_content = response.content or ""
        parsed = self.extract_json(raw_content)

        if not parsed:
            return self.fallback_decision(
                message=message,
                raw_response=raw_content,
                json_valid=False,
                schema_valid=False,
                model=response.model,
                tokens_used=response.tokens_used
            )

        schema_valid = self.validate_schema(parsed)

        if not schema_valid:
            return self.fallback_decision(
                message=message,
                raw_response=raw_content,
                json_valid=True,
                schema_valid=False,
                model=response.model,
                tokens_used=response.tokens_used
            )

        intent = parsed.get("intent", "general")

        if intent not in self.VALID_INTENTS:
            parsed["intent"] = "general"

        parsed["json_valid"] = True
        parsed["schema_valid"] = True
        parsed["raw_response"] = raw_content
        parsed["tokens_used"] = response.tokens_used
        parsed["model"] = response.model

        return parsed

    def extract_json(self, text: str):
        try:
            return json.loads(text)
        except Exception:
            pass

        match = re.search(r"\{.*\}", text, re.DOTALL)

        if not match:
            return None

        try:
            return json.loads(match.group(0))
        except Exception:
            return None

    def validate_schema(self, data: dict) -> bool:
        required_fields = [
            "intent",
            "action",
            "confidence",
            "entities",
            "needs_profile",
            "reason"
        ]

        for field in required_fields:
            if field not in data:
                return False

        if not isinstance(data["intent"], str):
            return False

        if not isinstance(data["action"], str):
            return False

        if not isinstance(data["entities"], dict):
            return False

        if not isinstance(data["needs_profile"], bool):
            return False

        return True

    def fallback_decision(
        self,
        message: str,
        raw_response: str,
        json_valid: bool,
        schema_valid: bool,
        model: str = "unknown",
        tokens_used: int = 0
    ) -> dict:

        fallback_intent = self.rule_based_backup(message)

        return {
            "intent": fallback_intent,
            "action": "fallback",
            "confidence": 0.35,
            "entities": {
                "items": [],
                "old_name": None,
                "new_name": None
            },
            "needs_profile": False,
            "reason": (
                "El LLM no devolvió JSON válido. "
                "Se usó respaldo por reglas para no romper el flujo."
            ),
            "json_valid": json_valid,
            "schema_valid": schema_valid,
            "raw_response": raw_response,
            "tokens_used": tokens_used,
            "model": model
        }

    def rule_based_backup(self, message: str) -> str:
        text = message.lower().strip()

        if any(word in text for word in [
            "inventario",
            "qué tengo",
            "que tengo",
            "qué hay",
            "que hay",
            "productos",
            "comida tengo",
            "alacena",
            "despensa"
        ]):
            return "inventory"

        if any(word in text for word in [
            "agrega",
            "añade",
            "mete",
            "compré",
            "compre",
            "agregué",
            "agregue",
            "registrar producto",
            "tengo ahora"
        ]):
            return "add_inventory"

        if any(word in text for word in [
            "elimina",
            "quita",
            "borra",
            "ya no tengo",
            "me comí",
            "me comi",
            "consumí",
            "consumi",
            "usé",
            "use",
            "gasté",
            "gaste"
        ]):
            return "remove_inventory"

        if any(word in text for word in [
            "cambia",
            "corrige",
            "renombra",
            "quise decir"
        ]):
            return "rename_inventory"

        if any(word in text for word in [
            "receta",
            "cocinar",
            "comer",
            "preparar"
        ]):
            return "recipe"

        if any(word in text for word in [
            "compras",
            "súper",
            "super",
            "qué falta",
            "que falta"
        ]):
            return "shopping"

        if any(word in text for word in [
            "plan semanal",
            "dieta",
            "plan alimenticio"
        ]):
            return "meal_plan"

        if any(word in text for word in [
            "calorías",
            "calorias",
            "macros",
            "proteína",
            "proteina",
            "tmb",
            "get"
        ]):
            return "nutrition"

        if any(word in text for word in [
            "consumir pronto",
            "echar a perder",
            "caducar",
            "caducarse"
        ]):
            return "reminders"

        if "registrar perfil" in text:
            return "profile_register"

        return "general"