from app.core.orchestrator import Orchestrator
from app.schemas.chat import ChatRequest
from app.schemas.tasks import TaskRunRequest, TaskRunResponse


class TaskService:
    def __init__(self, orchestrator: Orchestrator) -> None:
        self.orchestrator = orchestrator

    async def run(self, payload: TaskRunRequest) -> TaskRunResponse:
        result = await self.orchestrator.handle_chat(
            ChatRequest(
                prompt=payload.prompt,
                session_id=payload.session_id,
                allow_tools=True,
            )
        )
        return TaskRunResponse(
            task_type=result.route,
            status="completed",
            message=result.answer,
            session_id=result.session_id,
        )
