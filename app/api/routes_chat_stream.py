import json

from app.schemas.chat import ChatRequest
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/chat", tags=["chat"])


async def sse_body_generator(request: Request, payload: ChatRequest):
    orchestrator = request.app.state.orchestrator
    response = await orchestrator.handle_chat(payload)

    for run in response.tool_runs or []:
        data = json.dumps(
            {
                "name": run.name,
                "arguments": run.arguments,
                "result_preview": run.result_preview,
            },
            ensure_ascii=False,
        )
        yield f"event: tool_call\ndata: {data}\n\n"

    answer = response.answer or ""
    chunk_size = 8
    for i in range(0, len(answer), chunk_size):
        chunk = answer[i : i + chunk_size]
        token_payload = json.dumps(
            {"text": chunk, "route": response.route, "model": response.model_used},
            ensure_ascii=False,
        )
        yield f"event: token\ndata: {token_payload}\n\n"

    done_data = json.dumps(
        {
            "session_id": response.session_id,
            "route": response.route,
            "model_used": response.model_used,
            "total_chars": len(answer),
        },
        ensure_ascii=False,
    )
    yield f"event: done\ndata: {done_data}\n\n"


@router.post("/stream")
async def chat_stream(payload: ChatRequest, request: Request) -> StreamingResponse:
    return StreamingResponse(
        sse_body_generator(request=request, payload=payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
