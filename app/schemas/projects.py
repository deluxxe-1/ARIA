from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=2)
    description: str = Field(min_length=3)
    stack: str = Field(default="python-fastapi")


class ProjectCreateResponse(BaseModel):
    project_id: str
    name: str
    path: str
    readme_path: str
    message: str
