from typing import Protocol


class ReasoningProvider(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> str: ...
