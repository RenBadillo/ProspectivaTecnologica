from app.services.shopping_service import (
    ShoppingService
)


inventory = [

    {
        "name": "leche",
        "quantity": 1
    },

    {
        "name": "arroz",
        "quantity": 2
    }
]

service = ShoppingService()

shopping_list = (
    service.generate_shopping_list(
        inventory
    )
)

for item in shopping_list.items:

    print(
        item.priority,
        item.name,
        item.reason
    )