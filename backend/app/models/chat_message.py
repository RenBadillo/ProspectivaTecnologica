from dataclasses import dataclass


@dataclass
class ChatMessage:

    user_id: int

    role: str

    content: str

    timestamp: str