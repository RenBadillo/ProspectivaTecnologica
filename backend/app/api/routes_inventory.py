from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.inventory_service import InventoryService


router = APIRouter()
inventory_service = InventoryService()


class InventoryItem(BaseModel):
    nombre: str = Field(..., min_length=1)
    cantidad: int = Field(default=1, ge=1)
    fuente: str = "api"


@router.get("/inventory")
async def get_inventory_json():
    return {"inventory": inventory_service.load_inventory()}


@router.get("/inventory/db")
async def get_inventory_from_db():
    return {"inventory": inventory_service.load_inventory_from_db()}


@router.post("/inventory/add")
async def add_inventory_item(item: InventoryItem):
    inventory_service.add_food(item.nombre, item.cantidad, item.fuente)
    return {"message": "Alimento agregado al inventario"}


@router.post("/inventory/remove")
async def remove_inventory_item(item: InventoryItem):
    success = inventory_service.remove_food(item.nombre, item.cantidad)
    return {
        "message": "Alimento eliminado del inventario" if success else "No hay suficiente cantidad para eliminar"
    }
