import httpx

from app.models.inventory import Inventory


class PantryService:

    INVENTORY_URL = (
        "http://127.0.0.1:8000/inventory/db"
    )

    INVENTORY_ADD_URL = (
        "http://127.0.0.1:8000/inventory/add"
    )

    async def get_inventory(self):

        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:

            response = await client.get(
                self.INVENTORY_URL
            )

            response.raise_for_status()

            return response.json()

    async def add_product(
        self,
        name: str,
        quantity: int = 1
    ) -> bool:

        try:

            async with httpx.AsyncClient(
                timeout=10.0
            ) as client:

                response = await client.post(
                    self.INVENTORY_ADD_URL,
                    json={
                        "nombre": name,
                        "cantidad": quantity,
                        "fuente": "whatsapp"
                    }
                )

                response.raise_for_status()

                return True

        except:

            return False