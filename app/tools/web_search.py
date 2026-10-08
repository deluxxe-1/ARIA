import asyncio
from typing import Any

from duckduckgo_search import DDGS


def schema() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Busca informacion actual en internet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Consulta de busqueda."},
                },
                "required": ["query"],
            },
        },
    }


async def execute(query: str) -> dict[str, Any]:
    def _search() -> list[dict[str, Any]]:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=5))

    results = await asyncio.to_thread(_search)
    normalized = [
        {
            "title": item.get("title", ""),
            "url": item.get("href", ""),
            "snippet": item.get("body", ""),
        }
        for item in results
    ]
    return {"query": query, "results": normalized}
