from app.services.inventory_analysis_service import (
    InventoryAnalysisService
)

inventory = [

    {
        "name": "pollo",
        "quantity": 0
    },

    {
        "name": "arroz",
        "quantity": 1
    },

    {
        "name": "leche",
        "quantity": 5
    }
]

service = InventoryAnalysisService()

result = service.analyze_inventory(
    inventory
)

print(result)