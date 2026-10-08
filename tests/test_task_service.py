from unittest.mock import AsyncMock

import pytest

from app.schemas.chat import ChatResponse
from app.schemas.tasks import TaskRunRequest
from app.services.task_service import TaskService


async def test_task_service_uses_orchestrator_route() -> None:
    orchestrator = AsyncMock()
    orchestrator.handle_chat.return_value = ChatResponse(
        answer="respuesta",
        session_id="ses-123",
        route="code",
        model_used="qwen2.5-coder:7b",
        tool_runs=[],
    )
    service = TaskService(orchestrator=orchestrator)

    result = await service.run(
        TaskRunRequest(prompt="crea una api con fastapi", session_id="ses-123")
    )

    assert orchestrator.handle_chat.called
    assert orchestrator.handle_chat.await_count == 1
    assert result.task_type == "code"
    assert result.status == "completed"
    assert result.session_id == "ses-123"
    assert result.message == "respuesta"
