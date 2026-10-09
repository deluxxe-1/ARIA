from app.schemas.chat import ChatRequest, ChatResponse
from fastapi import APIRouter, Request

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    orchestrator = request.app.state.orchestrator
    return await orchestrator.handle_chat(payload)
