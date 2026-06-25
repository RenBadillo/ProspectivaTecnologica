from fastapi import APIRouter,Request
import json
from pathlib import Path
from app.vision.vision_llm import detectar_alimentos
from app.vision.vision_llm import obtener_json



IMAGE_PATH = (Path(__file__).resolve().parents[2] / "images" / "latest.jpg")

IMAGE_PATH.parent.mkdir(parents=True, exist_ok=True)

router = APIRouter()

@router.get("/vision")
async def root():
    return{
        "message": "¡Bienvenido a la API de visión por computadora!"
    }

@router.post("/vision/upload")
async def upload_image(request:Request):

    image = await request.body()

    IMAGE_PATH.write_bytes(image)

    return {
        "message": "Imagen recibida y guardada correctamente.",
        "image_path": str(IMAGE_PATH)
    }