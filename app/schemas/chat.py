from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1)
    session_id: str | None = None
    allow_tools: bool = True


class ToolExecution(BaseModel):
    name: str
    arguments: dict[str, Any]
    result_preview: str


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    route: str
    model_used: str
    tool_runs: list[ToolExecution] = Field(default_factory=list)
