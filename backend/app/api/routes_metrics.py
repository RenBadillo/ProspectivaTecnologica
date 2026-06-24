import time
from pydantic import BaseModel

from app.services.chat_router_service import ChatRouterService
from fastapi import APIRouter

from app.database.metrics_repository import MetricsRepository


router = APIRouter()
metrics_repository = MetricsRepository()

chat_router = ChatRouterService()


class IntentTestInput(BaseModel):
    message: str
    expected_intent: str

MODEL_PRICING = {
    "gpt-4o-mini": {
        "input_per_1m": 0.15,
        "output_per_1m": 0.60
    },
    "gpt-4o": {
        "input_per_1m": 5.00,
        "output_per_1m": 15.00
    },
    "claude-3-5-sonnet": {
        "input_per_1m": 3.00,
        "output_per_1m": 15.00
    },
    "gemini-1.5-pro": {
        "input_per_1m": 3.50,
        "output_per_1m": 10.50
    }
}


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model_name: str
) -> float:

    pricing = MODEL_PRICING[model_name]

    input_cost = (
        prompt_tokens / 1_000_000
    ) * pricing["input_per_1m"]

    output_cost = (
        completion_tokens / 1_000_000
    ) * pricing["output_per_1m"]

    return round(
        input_cost + output_cost,
        6
    )


@router.get("/metrics/summary")
async def get_metrics_summary():

    summary = metrics_repository.get_summary()

    llm = summary["llm"]

    prompt_tokens = llm.get("prompt_tokens") or 0
    completion_tokens = llm.get("completion_tokens") or 0

    cost_comparison = {}

    for model_name in MODEL_PRICING:
        cost_comparison[model_name] = estimate_cost(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model_name=model_name
        )

    return {
        "summary": summary,
        "cost_comparison": cost_comparison,
        "local_ollama_cost": 0
    }


@router.get("/metrics/chat-history")
async def get_chat_history():
    return {
        "history": metrics_repository.get_chat_history(
            limit=100
        )
    }


@router.get("/metrics/llm-history")
async def get_llm_history():
    return {
        "history": metrics_repository.get_llm_metrics(
            limit=100
        )
    }

@router.get("/metrics/inventory-summary")
async def get_inventory_summary():
    return {
        "summary": metrics_repository.get_inventory_summary()
    }


@router.get("/metrics/inventory-history")
async def get_inventory_history():
    return {
        "history": metrics_repository.get_inventory_chat_history(
            limit=100
        )
    }

@router.post("/metrics/intent-test")
async def run_intent_test(
    test: IntentTestInput
):
    start_time = time.perf_counter()

    detected_intent = chat_router.classify(
        test.message
    )

    response = ""

    if detected_intent == "inventory":
        response = chat_router.handle_inventory()

    latency_seconds = round(
        time.perf_counter() - start_time,
        4
    )

    metrics_repository.save_intent_test(
        message=test.message,
        expected_intent=test.expected_intent,
        detected_intent=detected_intent,
        response=response,
        latency_seconds=latency_seconds
    )

    return {
        "message": test.message,
        "expected_intent": test.expected_intent,
        "detected_intent": detected_intent,
        "response": response,
        "latency_seconds": latency_seconds,
        "is_correct": test.expected_intent == detected_intent,
        "has_response": bool(response.strip())
    }


@router.get("/metrics/intent-tests")
async def get_intent_tests():
    return {
        "summary": metrics_repository.get_intent_test_summary(),
        "tests": metrics_repository.get_intent_tests(
            limit=100
        )
    }


@router.post("/metrics/run-inventory-tests")
async def run_inventory_tests():

    test_messages = [
        "dame el inventario",
        "qué tengo en mi alacena",
        "que tengo en mi alacena",
        "qué productos tengo",
        "que productos tengo",
        "qué comida tengo",
        "que comida tengo",
        "qué hay en mi despensa",
        "que hay en mi despensa",
        "mis productos disponibles"
    ]

    results = []

    for message in test_messages:
        start_time = time.perf_counter()

        detected_intent = chat_router.classify(
            message
        )

        response = ""

        if detected_intent == "inventory":
            response = chat_router.handle_inventory()

        latency_seconds = round(
            time.perf_counter() - start_time,
            4
        )

        metrics_repository.save_intent_test(
            message=message,
            expected_intent="inventory",
            detected_intent=detected_intent,
            response=response,
            latency_seconds=latency_seconds
        )

        results.append({
            "message": message,
            "expected_intent": "inventory",
            "detected_intent": detected_intent,
            "response": response,
            "latency_seconds": latency_seconds,
            "is_correct": detected_intent == "inventory",
            "has_response": bool(response.strip())
        })

    return {
        "results": results,
        "summary": metrics_repository.get_intent_test_summary()
    }

@router.get("/metrics/real-chat-analysis")
async def get_real_chat_analysis():
    return {
        "history": metrics_repository.get_real_chat_analysis(
            limit=100
        )
    }