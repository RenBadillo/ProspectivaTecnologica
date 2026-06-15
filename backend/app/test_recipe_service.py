import asyncio



from app.services.recipe_service import (
    RecipeService
)


async def main():

    service = RecipeService()

    recipe = await service.generate_recipe(
    "5215512345678"
)

    print(recipe)


asyncio.run(main())