from dataclasses import dataclass


@dataclass
class LLMResponse:

    success: bool

    content: str

    tokens_used: int = 0

    model: str = ""