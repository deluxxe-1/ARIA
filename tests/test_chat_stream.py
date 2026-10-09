import json
from typing import Any
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.core.settings import get_settings
from app.main import create_app
from app.schemas.chat import ChatResponse, ToolExecution


def _read_sse_events(body_bytes: bytes) -> list[tuple[str, dict]]:
    text = body_bytes.decode("utf-8")
    blocks = text.split("\n\n")
    events: list[tuple[str, dict]] = []
    for block in blocks:
        if not block.strip():
            continue
        event_type: str | None = None
        data_str: str | None = None
        for line in block.split("\n"):
            if line.startswith("event: "):
                event_type = line[len("event: "):]
            elif line.startswith("data: "):
                data_str = line[len("data: "):]
        if event_type is not None and data_str is not None:
            events.append((event_type, json.loads(data_str)))
    return events


async def _fake_handle_chat(payload: Any) -> ChatResponse:
    return ChatResponse(
        answer="Hola mundo streaming",
        session_id="abc",
        route="general",
        model_used="planner",
        tool_runs=[
            ToolExecution(
                name="tool1",
                arguments={"k": "v"},
                result_preview="preview1",
            )
        ],
    )


def test_chat_stream_sse_events_structure() -> None:
    get_settings.cache_clear()
    app = create_app()
    with TestClient(app, raise_server_exceptions=False, follow_redirects=False) as client:
        orchestrator = client.app.state.orchestrator
        orchestrator.handle_chat = AsyncMock(side_effect=_fake_handle_chat)

        payload = {"prompt": "hola", "allow_tools": True}
        with client.stream("POST", "/chat/stream", json=payload) as r:
            assert r.status_code == 200, r.text
            assert r.headers["content-type"].startswith("text/event-stream")
            raw = b"".join(r.iter_bytes())

    events = _read_sse_events(raw)

    tool_call_events = [e for e in events if e[0] == "tool_call"]
    token_events = [e for e in events if e[0] == "token"]
    done_events = [e for e in events if e[0] == "done"]

    assert len(tool_call_events) == 1
    assert tool_call_events[0][1]["name"] == "tool1"
    assert tool_call_events[0][1]["arguments"] == {"k": "v"}
    assert tool_call_events[0][1]["result_preview"] == "preview1"

    assert len(token_events) >= 1
    for _, token_data in token_events:
        assert "text" in token_data
        assert token_data["route"] == "general"
        assert token_data["model"] == "planner"

    assert len(done_events) == 1
    assert done_events[0][1]["session_id"] == "abc"
    assert done_events[0][1]["route"] == "general"
    assert done_events[0][1]["model_used"] == "planner"
    assert done_events[0][1]["total_chars"] == len("Hola mundo streaming")

    event_order = [e[0] for e in events]
    first_tool = event_order.index("tool_call")
    first_token = event_order.index("token")
    first_done = event_order.index("done")
    assert first_tool < first_token < first_done
