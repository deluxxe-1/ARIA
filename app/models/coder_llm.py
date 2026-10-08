from pathlib import Path
from typing import Any

from app.models.ollama_client import OllamaClient


def _read_prompt(filename: str) -> str:
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / filename
    return prompt_path.read_text(encoding="utf-8")


class CoderLLM:
    def __init__(self, client: OllamaClient, model_name: str) -> None:
        self.client = client
        self.model_name = model_name
        self.system_prompt = _read_prompt("coder_system.txt")

    async def generate(self, history: list[dict[str, Any]], prompt: str, plan: str) -> str:
        coder_prompt = (
            "Usa este plan como contexto y devuelve la mejor respuesta tecnica posible.\n\n"
            f"Plan del planner:\n{plan}\n\n"
            f"Peticion del usuario:\n{prompt}"
        )
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            *history,
            {"role": "user", "content": coder_prompt},
        ]
        response = await self.client.chat(model=self.model_name, messages=messages)
        return response.get("message", {}).get("content", "").strip()
