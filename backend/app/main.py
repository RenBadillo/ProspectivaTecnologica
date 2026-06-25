import time
from typing import Dict

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.api.routes_inventory import router as inventory_router
from app.api.routes_chat import router as chat_router
from app.api.routes_metrics import router as metrics_router
from app.api.routes_orchestrator import router as orchestrator_router
from app.api.routes_vision import router as vision_router

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"

COPILOT_PROFILES: Dict[str, Dict[str, str]] = {
    "generico": {
        "label": "Asistente genérico",
        "system_prompt": (
            "Eres un asistente de alacena inteligente. "
            "Respondes preguntas generales sobre el inventario, recetas y compras. "
            "Usa lenguaje claro y amigable. Si no tienes información suficiente, pregunta antes de asumir."
        ),
    },
    "administrador": {
        "label": "Administrador de alacena",
        "system_prompt": (
            "Eres el administrador de una alacena inteligente. "
            "Tu rol es gestionar el inventario de productos: agregar, consultar y reportar existencias. "
            "Cuando el usuario reporte productos nuevos, confirma qué se agregó. "
            "Cuando consulte el inventario, preséntalo de forma organizada por categorías si es posible. "
            "Advierte cuando un producto esté por agotarse (cantidad menor a 2). "
            "Responde de forma precisa, sin inventar cantidades ni productos. "
            "Si falta información sobre un producto, pregunta antes de registrarlo."
        ),
    },
    "nutriologo": {
        "label": "Nutriólogo virtual",
        "system_prompt": (
            "Eres un nutriólogo virtual especializado en alimentación saludable. "
            "Tu rol es analizar el inventario de la alacena del usuario y sugerir recetas balanceadas, "
            "combinaciones nutritivas y hábitos alimenticios saludables. "
            "Considera macronutrientes, vitaminas y balance calórico en tus sugerencias. "
            "Siempre explica brevemente el valor nutricional de los ingredientes que uses. "
            "No diagnostiques enfermedades ni sustituyas consulta médica. "
            "Si el inventario tiene pocos ingredientes, sugiere qué comprar para mejorar el balance nutricional. "
            "Responde en español con tono profesional pero accesible."
        ),
    },
    "comprador": {
        "label": "Asistente de compras",
        "system_prompt": (
            "Eres un asistente de compras inteligente para una alacena familiar. "
            "Tu rol es generar listas de compras organizadas, prácticas y económicas. "
            "Cuando el usuario comparta su inventario actual, analiza qué falta para una semana completa de comidas. "
            "Organiza la lista de compras por categorías: frutas y verduras, proteínas, lácteos, abarrotes, otros. "
            "Estima cantidades razonables para una familia de 4 personas por defecto, "
            "pero ajusta si el usuario indica diferente. "
            "Sugiere marcas o presentaciones económicas cuando sea relevante. "
            "Responde en español de forma clara y estructurada."
        ),
    },
}

app = FastAPI(
    title="Alacena Inteligente — Copilotos especializados",
    description="API con perfiles de copiloto para la alacena inteligente.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventory_router)
app.include_router(chat_router)
app.include_router(metrics_router)
app.include_router(orchestrator_router)
app.include_router(vision_router)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    model: str = Field(default="llama3.2:3b", min_length=1, max_length=100)
    copilot_profile: str = Field(default="generico", min_length=1, max_length=50)
    system_prompt: str = Field(default="", max_length=6000)
    temperature: float = Field(default=0.7, ge=0.0, le=1.2)
    top_p: float = Field(default=0.9, ge=0.1, le=1.0)
    num_predict: int = Field(default=180, ge=20, le=1000)
    num_ctx: int = Field(default=4096, ge=512, le=8192)
    repeat_penalty: float = Field(default=1.1, ge=1.0, le=2.0)
    keep_alive: str = Field(default="5m", max_length=20)


@app.get("/")
def root():
    return {"message": "Alacena Inteligente API funcionando", "docs": "/docs", "profiles": "/profiles"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/profiles")
def profiles():
    return COPILOT_PROFILES

@app.post("/chat/admin")
def chat_admin(request: ChatRequest):
    if request.copilot_profile not in COPILOT_PROFILES:
        raise HTTPException(status_code=400, detail=f"Perfil no válido: {request.copilot_profile}")

    profile = COPILOT_PROFILES[request.copilot_profile]
    system_prompt_used = request.system_prompt.strip() or profile["system_prompt"]

    payload = {
        "model": request.model.strip(),
        "messages": [
            {"role": "system", "content": system_prompt_used},
            {"role": "user", "content": request.message},
        ],
        "stream": False,
        "keep_alive": request.keep_alive,
        "options": {
            "temperature": request.temperature,
            "top_p": request.top_p,
            "num_predict": request.num_predict,
            "num_ctx": request.num_ctx,
            "repeat_penalty": request.repeat_penalty,
        },
    }

    try:
        start = time.perf_counter()
        response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=300)
        wall = time.perf_counter() - start
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="No se pudo conectar con Ollama.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    ed = data.get("eval_duration", 0) / 1e9
    ec = data.get("eval_count", 0)

    return {
        "model": request.model,
        "copilot_profile": request.copilot_profile,
        "copilot_label": profile["label"],
        "system_prompt_used": system_prompt_used,
        "reply": data.get("message", {}).get("content", ""),
        "metrics": {
            "wall_time_s": round(wall, 3),
            "total_duration_s": round(data.get("total_duration", 0) / 1e9, 3),
            "load_duration_s": round(data.get("load_duration", 0) / 1e9, 3),
            "prompt_eval_count": data.get("prompt_eval_count", 0),
            "eval_count": ec,
            "total_tokens": data.get("prompt_eval_count", 0) + ec,
            "eval_duration_s": round(ed, 3),
            "tokens_per_second": round(ec / ed if ed > 0 else 0, 2),
        }
    }