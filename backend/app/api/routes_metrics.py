from fastapi import APIRouter

from app.database.metrics_repository import MetricsRepository


router = APIRouter()
metrics_repository = MetricsRepository()


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