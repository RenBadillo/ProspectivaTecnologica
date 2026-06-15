from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.chat_router_service import ChatRouterService


router = APIRouter()
historial = []
chat_router = ChatRouterService()


class MensajeEntrada(BaseModel):
    numero: str = Field(..., min_length=1)
    mensaje: str = Field(..., min_length=1)


class RespuestaChat(BaseModel):
    numero: str
    respuesta: str


@router.post("/chat", response_model=RespuestaChat)
async def recibir_mensaje(entrada: MensajeEntrada):
    if not entrada.mensaje.strip():
        raise HTTPException(status_code=400, detail="Mensaje vacío")

    respuesta = await chat_router.handle_message(entrada.numero, entrada.mensaje)

    historial.append({
        "numero": entrada.numero,
        "mensaje": entrada.mensaje,
        "respuesta": respuesta,
    })

    return RespuestaChat(numero=entrada.numero, respuesta=respuesta)


@router.get("/chat/historial")
async def ver_historial():
    return {"total": len(historial), "mensajes": historial}


@router.get("/chat/health")
async def health():
    return {"status": "ok", "servicio": "chat"}
