import httpx

from app.models.llm_response import LLMResponse


class LLMService:
    """Cliente único para hablar con Ollama.

    Ningún otro service debería usar httpx directamente para llamar al LLM.
    """

    def __init__(
        self,
        model: str = "llama3.2:3b",
        url: str = "http://localhost:11434/api/generate"
    ):
        self.model = model
        self.url = url

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 350,
        timeout: float = 180.0
    ) -> LLMResponse:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self.url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                            "top_p": 0.9,
                            "repeat_penalty": 1.1,
                            "num_ctx": 2048,
                        },
                    },
                )
                response.raise_for_status()
                data = response.json()

                return LLMResponse(
                    success=True,
                    content=data.get("response", "").strip(),
                    tokens_used=data.get("eval_count", 0),
                    model=self.model,
                )

        except httpx.ConnectError:
            return LLMResponse(
                success=False,
                content="No se pudo conectar con Ollama. Verifica que 'ollama serve' esté corriendo.",
                model=self.model,
            )
        except httpx.HTTPStatusError as exc:
            return LLMResponse(
                success=False,
                content=f"Error HTTP al llamar a Ollama: {exc.response.status_code} {exc.response.text}",
                model=self.model,
            )
        except Exception as exc:
            return LLMResponse(
                success=False,
                content=f"Error inesperado al llamar al LLM: {exc}",
                model=self.model,
            )
