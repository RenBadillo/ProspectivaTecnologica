import time
import httpx

from app.models.llm_response import LLMResponse
from app.database.metrics_repository import MetricsRepository


class LLMService:

    def __init__(
        self,
        model: str = "llama3.2:3b"
    ):

        self.model = model
        self.url = "http://localhost:11434/api/generate"
        self.metrics_repository = MetricsRepository()

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.4,
        max_tokens: int = 500
    ) -> LLMResponse:

        start_time = time.perf_counter()

        try:

            async with httpx.AsyncClient(
                timeout=120.0
            ) as client:

                response = await client.post(
                    self.url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    }
                )

                response.raise_for_status()

                data = response.json()

                content = (
                    data
                    .get("response", "")
                    .strip()
                )

                latency_seconds = round(
                    time.perf_counter() - start_time,
                    4
                )

                prompt_tokens = int(
                    data.get("prompt_eval_count", 0)
                )

                completion_tokens = int(
                    data.get("eval_count", 0)
                )

                total_tokens = (
                    prompt_tokens
                    + completion_tokens
                )

                tokens_per_second = 0

                if latency_seconds > 0:
                    tokens_per_second = round(
                        completion_tokens / latency_seconds,
                        4
                    )

                self.metrics_repository.save_llm_metric(
                    model=self.model,
                    provider="ollama",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    latency_seconds=latency_seconds,
                    tokens_per_second=tokens_per_second
                )

                return LLMResponse(
                    success=True,
                    content=content,
                    tokens_used=total_tokens,
                    model=self.model
                )

        except Exception as error:

            return LLMResponse(
                success=False,
                content=str(error),
                tokens_used=0,
                model=self.model
            )