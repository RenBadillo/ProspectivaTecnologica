from google import genai
from PIL import Image
import os
from dotenv import load_dotenv
import json
from pathlib import Path


load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY is None:
    raise RuntimeError("No se encontró GEMINI_API_KEY en el archivo .env")

client = genai.Client(api_key=API_KEY)


IMAGE_PATH = (Path(__file__).resolve().parents[2] / "images" / "latest.jpg")

IMAGE_PATH.parent.mkdir(parents=True, exist_ok=True)

def detectar_alimentos(image_path:str):

    image = Image.open(image_path)

    prompt = """
    Analiza únicamente los alimentos visibles.

    Responde solo y exclusivamente con el siguiente formato JSON:

    {
        "foods":[
            {
                "name":"",
                "confidence":0,
                "quantity":""
            }
        ]
    }
    
    No inventes alimentos.
    Los unicos alimentos que puedes responder son los siguientes: 
    Paquete Danonino 
    Paquete Gelatina Dany 
    Jugo mango Jumex
    Cereal Trix 
    Cartón Nutri Leche 
    Cartón LALA leche 
    Aceite Nutrioli
    Botella Bonafont 
    Chocolate Larín
    Mantequilla Primavera
    ChocoMIlk
    Paquete Espagueti 
    Jugo de fresa Boing 
    Papas Pringles
    Jugo mango del Valle
    Salsa de tomate
    Mayonesa Mccormick
    Sal La fina 
    Jugo Fusetea
    Jugo pera Jumex
    Bebida Energetica Red bull
    Refresco CocaCola

    No respondas con alimentos que no estén en la lista.
    
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            image,
            prompt
        ],
        config={
        "response_mime_type": "application/json"
        }
    )

    return obtener_json(response)


def obtener_json(response):

    try:

        data = json.loads(response.text)

        return data

    except json.JSONDecodeError as e:


        print(e)


        return {
            "foods": [],
            "error": "Gemini devolvió un JSON inválido",
        }