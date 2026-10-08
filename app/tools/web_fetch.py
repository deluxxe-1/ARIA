from typing import Any

import httpx
from bs4 import BeautifulSoup


def schema() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Descarga una URL y devuelve un resumen legible del contenido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL completa a descargar."},
                },
                "required": ["url"],
            },
        },
    }


async def execute(url: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    return {
        "url": url,
        "content": text[:5000],
    }
