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

FOODS_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "foods.json"
)

with open(FOODS_PATH, encoding="utf-8") as f:
    FOODS = json.load(f)

IMAGE_PATH.parent.mkdir(parents=True, exist_ok=True)

food_list = "\n".join(FOODS.keys())

def detectar_alimentos(image_path:str):

    image = Image.open(image_path)

    prompt = f"""
        Analiza únicamente los alimentos o productos visibles.

        Los únicos nombres permitidos son exactamente los siguientes:

        {food_list}

        Reglas:

        1. El campo "name" debe ser exactamente uno de los nombres anteriores.
        2. No inventes productos o alimentos.
        3. Si un alimento no aparece en la lista o si no puedes identificar con alta confianza un producto, no lo incluyas.
        4. Si el texto del empaque no es legible o la marca no puede distinguirse claramente, NO adivines. Es preferible devolver una lista vacía que identificar un producto incorrecto.
        5. Devuelve únicamente JSON válido.
        6. No deduzcas el contenido de un envase parcialmente oculto.

        Descripción visual de cada articulo de apoyo:
        Refresco Ameyal: Botella color rosa.
        Paquete Gelatina Dany: Dos vasos morados.
        Jugo de Mango Jumex: Caja azul con un mango amarillo.
        Cereal Trix: Caja predominantemente roja, tiene el logo de trix en verde.
        Cartón de Nutri Leche: Caja blanca con con el logo de nutrileche con letras blancas.
        Cartón LALA leche: Caja blanca con el logo de lala en color azul, tiene una franja roja abajo del logo.
        Aceite Nutrioli: Botella de color dorado con etiqueta y tapa verdes.
        Botella Bonafont: Botella de agua transparente.
        Chocolate Larín: Barra de color verde.
        Mantequilla Primavera: Barra de color amarillo.
        ChocoMilk: Lata cilindrica de color azul.
        Paquete Espagueti: Paquete transparente con logo amarillo con negro, se puede ver el espagueti crudo de color amarillo obscuro.
        Jugo de fresa Boing: Lata de color rojo y letras verdes.
        Papas Pringles: Lata de color rojo con letras y logo blanco.
        Jugo de mango del Valle: Lata de color amarillo con logo negro con blanco.
        Salsa de tomate: Lata negra con logo rojo.
        Mayonesa McCormick: Frasco blanco con etiqueta y tapa rojas.
        Sal La Fina: Frasco blanco con etqueta azul con rojo y tapa amarilla.
        Jugo FuseTea: Lata amarilla con letras negras.
        Jugo pera Jumex: Lata azul con logo verde, rojo y verde.
        Bebida Energética Red Bull: Lata azul con gris y logo rojo con amarillo.
        Refresco CocaCola: Botella negra con etiqueta roja.
        Cereal Nesquik: Caja amarilla con logo café y azul.
        Cereal ChocoKrispis: Caja café con logo de letras amarillas.
        Refresco Fanta: lata de color naranja con logo de letras verdes

        La lista de apoyo anterior solo es de apoyo, no infieras productos solo por el color. 
        La marca o el texto del empaque deben ser visibles, o bien la apariencia debe coincidir claramente con la descripción visual.

        Formato:

        {{
        "foods":[
            {{
            "name":"",
            "confidence":0,
            "quantity":""
            }}
        ]
        }}
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