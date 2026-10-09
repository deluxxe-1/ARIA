from app.schemas.tasks import TaskRunRequest, TaskRunResponse
from fastapi import APIRouter, Request

router = APIRouter(tags=["tasks"])


@router.post("/task/run", response_model=TaskRunResponse)
async def run_task(payload: TaskRunRequest, request: Request) -> TaskRunResponse:
    task_service = request.app.state.task_service
    return await task_service.run(payload)
