from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ChatMemory(Protocol):
    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model: str | None = None,
        route: str | None = None,
    ) -> None: ...

    async def get_recent_messages(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]: ...


@runtime_checkable
class LLMProvider(Protocol):
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]: ...
