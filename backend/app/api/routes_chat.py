import time

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.chat_router_service import ChatRouterService
from app.database.metrics_repository import MetricsRepository


router = APIRouter()

chat_router = ChatRouterService()
metrics_repository = MetricsRepository()


class ChatInput(BaseModel):
    numero: str
    mensaje: str


@router.get("/chat/health")
async def chat_health():
    return {
        "status": "chat ok"
    }


@router.post("/chat")
async def recibir_mensaje(
    entrada: ChatInput
):
    start_time = time.perf_counter()

    try:
        result = await chat_router.handle_message(
            entrada.numero,
            entrada.mensaje
        )

        if isinstance(result, dict):
            respuesta = result.get("respuesta", "")
            intent = result.get("intent", "general")
            orchestrator = result.get("orchestrator", {})
        else:
            respuesta = result
            intent = chat_router.classify(entrada.mensaje)
            orchestrator = {}

        latency_seconds = round(
            time.perf_counter() - start_time,
            4
        )

        metrics_repository.save_chat_message(
            numero=entrada.numero,
            mensaje=entrada.mensaje,
            respuesta=respuesta,
            intent=intent,
            latency_seconds=latency_seconds,
            success=True,
            error=None,
            orchestrator=orchestrator
        )

        return {
            "numero": entrada.numero,
            "respuesta": respuesta,
            "intent": intent,
            "latency_seconds": latency_seconds,
            "orchestrator": orchestrator
        }

    except Exception as error:
        latency_seconds = round(
            time.perf_counter() - start_time,
            4
        )

        metrics_repository.save_chat_message(
            numero=entrada.numero,
            mensaje=entrada.mensaje,
            respuesta="",
            intent="error",
            latency_seconds=latency_seconds,
            success=False,
            error=str(error),
            orchestrator=orchestrator
        )

        raise error


@router.get("/chat/historial")
async def obtener_historial():
    mensajes = metrics_repository.get_chat_history(
        limit=100
    )

    return {
        "mensajes": mensajes
    }