from app.services.inventory_service import InventoryService
from app.services.nutrition_service import NutritionService
from app.services.llm_service import LLMService
from app.database.user_repository import UserRepository
from app.utils.prompt_manager import PromptManager
from app.utils.inventory_formatter import InventoryFormatter


class RecipeService:

    def __init__(self):

        self.inventory_service = InventoryService()
        self.user_repository = UserRepository()
        self.nutrition_service = NutritionService()
        self.llm_service = LLMService()

    async def generate_recipe(
        self,
        whatsapp_number: str
    ) -> str:

        user = self.user_repository.get_by_whatsapp(
            whatsapp_number
        )

        if not user:
            return (
                "No encontré un perfil nutricional para este número. "
                "Primero registra los datos del usuario."
            )

        inventory = (
            self.inventory_service
            .load_inventory_from_db()
        )

        available_ingredients = (
            InventoryFormatter
            .get_available_names(inventory)
        )

        if not available_ingredients:
            return (
                "Tu inventario está vacío. "
                "Agrega alimentos primero para poder generar una receta."
            )

        nutrition = (
            self.nutrition_service
            .generate_profile(user)
        )

        base_prompt = PromptManager.load(
            "recipe_prompt.txt"
        )

        inventory_text = (
            InventoryFormatter
            .to_prompt(inventory)
        )

        final_prompt = f"""
{base_prompt}

INGREDIENTES DISPONIBLES:
{inventory_text}

LISTA ESTRICTA DE INGREDIENTES PERMITIDOS:
{", ".join(available_ingredients)}

PERFIL DEL USUARIO:
Nombre: {user.name}
Objetivo: {user.goal}
Restricciones: {user.dietary_restrictions}
Preferencias: {user.food_preferences}

OBJETIVOS DIARIOS DEL USUARIO:
Calorías diarias objetivo: {nutrition.calories_target}
Proteínas diarias objetivo: {nutrition.protein_target}
Carbohidratos diarios objetivo: {nutrition.carb_target}
Grasas diarias objetivo: {nutrition.fat_target}

IMPORTANTE:
No copies estos valores como si fueran los nutrientes de la receta.
La información nutrimental de la receta debe ser una estimación aproximada solo del platillo generado.

INSTRUCCIÓN FINAL:
La receta principal debe usar únicamente ingredientes de la lista permitida.
No tienes que usar todo el inventario disponible.
Usa cantidades razonables por porción.
La información nutrimental debe estimar una porción normal de la receta, no todo el inventario.
Si mencionas ingredientes no disponibles, deben aparecer solo como opcionales.
"""

        response = await self.llm_service.generate(
            prompt=final_prompt,
            temperature=0.2,
            max_tokens=550
        )

        if not response.success:
            return (
                "Hubo un problema al generar la receta: "
                f"{response.content}"
            )

        return response.content