#esta funcion servirá para aplicar cambios a la bd a partir de lo que detecte la camara

from app.services.inventory_service import InventoryService
from app.vision.vision_camera import visionCamera
from app.vision.vision_llm import detectar_alimentos


class VisionInventory:

    def __init__(self):
        self.camera = visionCamera()
        self.inventoryServ = InventoryService()


    def sync_inventory(self):
        path = self.camera.capture()
        detected = detectar_alimentos(path)

        current = self.inventoryServ.load_inventory_from_db()

        changes = self.compare_inv(
            current,
            detected
        )

        self.apply_changes(changes)

        return changes
    
    def compare_inv(self,current,detected):

        inventory_current_names = {self.normalize(item["name"]) for item in current}

        inventory_detected_names = {self.normalize(item["name"]) for item in detected["foods"]}

        faltantes = inventory_current_names - inventory_detected_names

        presentes = inventory_detected_names & inventory_current_names

        nuevos = inventory_detected_names - inventory_current_names

        return {
            "faltantes":list(faltantes),
            "presentes":list(presentes),
            "nuevos":list(nuevos)

        }

    def normalize(self, name):

        name = name.lower()

        replacements = {
            "á":"a",
            "é":"e",
            "í":"i",
            "ó":"o",
            "ú":"u"
        }

        for old,new in replacements.items():
            name = name.replace(old,new)

        return name.strip()
    
    def apply_changes(self,changes):

        print("Faltantes")
            
        for food in changes["faltantes"]: print(food)

        print("Presentes")

        for food in changes["presentes"]: print(food)

        print("Nuevos")

        for food in changes["nuevos"]: print(food)



        

    



        
        

        