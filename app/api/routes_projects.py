from fastapi import APIRouter, Request

from app.schemas.projects import ProjectCreateRequest, ProjectCreateResponse


router = APIRouter(tags=["projects"])


@router.post("/project/create", response_model=ProjectCreateResponse)
async def create_project(payload: ProjectCreateRequest, request: Request) -> ProjectCreateResponse:
    project_service = request.app.state.project_service
    return project_service.create_project(payload)
