from fastapi import APIRouter
from pydantic import BaseModel

from app.services.orchestrator_service import OrchestratorService

router = APIRouter()

orchestrator = OrchestratorService()


class TestMessage(BaseModel):
    mensaje: str


@router.post("/orchestrator/test")
async def test_orchestrator(data: TestMessage):

    decision = await orchestrator.decide(
        data.mensaje
    )

    return decision