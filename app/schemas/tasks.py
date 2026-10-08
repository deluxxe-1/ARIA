from pydantic import BaseModel, Field


class TaskRunRequest(BaseModel):
    prompt: str = Field(min_length=1)
    session_id: str | None = None


class TaskRunResponse(BaseModel):
    task_type: str
    status: str
    message: str
    session_id: str
