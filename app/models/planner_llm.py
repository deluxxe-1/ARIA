from pathlib import Path
from typing import Any

from app.models.ollama_client import OllamaClient


def _read_prompt(filename: str) -> str:
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / filename
    return prompt_path.read_text(encoding="utf-8")


class PlannerLLM:
    def __init__(self, client: OllamaClient, model_name: str) -> None:
        self.client = client
        self.model_name = model_name
        self.system_prompt = _read_prompt("planner_system.txt")

    def build_messages(self, history: list[dict[str, Any]], prompt: str) -> list[dict[str, Any]]:
        return [
            {"role": "system", "content": self.system_prompt},
            *history,
            {"role": "user", "content": prompt},
        ]

    async def chat(
        self,
        history: list[dict[str, Any]],
        prompt: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        messages = self.build_messages(history=history, prompt=prompt)
        return await self.client.chat(
            model=self.model_name,
            messages=messages,
            tools=tools,
        )

    async def plan_for_code(self, history: list[dict[str, Any]], prompt: str) -> str:
        planning_prompt = (
            "Crea un plan breve y accionable para que el modelo coder resuelva esta tarea.\n\n"
            f"Tarea:\n{prompt}"
        )
        response = await self.chat(history=history, prompt=planning_prompt)
        return response.get("message", {}).get("content", "").strip()
