from typing import Any

import httpx


class OllamaClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=10),
            timeout=httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=5.0),
        )

    async def aclose(self) -> None:
        try:
            await self._client.aclose()
        except Exception:
            pass

    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if tools:
            payload["tools"] = tools

        response = await self._client.post(f"{self.base_url}/api/chat", json=payload)
        response.raise_for_status()
        return response.json()

    async def tags(self) -> dict[str, Any]:
        response = await self._client.get(f"{self.base_url}/api/tags")
        response.raise_for_status()
        return response.json()
