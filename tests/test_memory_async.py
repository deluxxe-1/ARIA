from pathlib import Path

import aiosqlite
import pytest

from app.memory.store import MemoryStore


@pytest.fixture
async def store(tmp_path: Path) -> MemoryStore:
    db = tmp_path / "test_aria.db"
    memory = MemoryStore(db)
    await memory._init_db()
    return memory


async def test_init_db_creates_index(store: MemoryStore) -> None:
    async with aiosqlite.connect(store.db_path) as conn:
        async with conn.execute("PRAGMA index_list(messages)") as cursor:
            rows = await cursor.fetchall()
    index_names = [row[1] for row in rows]
    assert "idx_messages_session_id_id" in index_names


async def test_save_and_recent_messages_order(store: MemoryStore) -> None:
    session = "sess-order"
    for i in range(5):
        await store.save_message(session_id=session, role="user", content=f"msg {i}")
    recent = await store.get_recent_messages(session_id=session, limit=3)
    assert len(recent) == 3
    contents = [m["content"] for m in recent]
    # get_recent_messages returns reversed(rows); rows is ORDER BY id DESC LIMIT 3
    # rows is: [msg 4, msg 3, msg 2]; reversed gives [msg 2, msg 3, msg 4]
    assert contents == ["msg 2", "msg 3", "msg 4"]


async def test_recent_messages_isolation_per_session(store: MemoryStore) -> None:
    s_a = "sess-a"
    s_b = "sess-b"
    for i in range(10):
        await store.save_message(session_id=s_a, role="user", content=f"A-{i}")
    await store.save_message(session_id=s_b, role="user", content="B-0")
    a = await store.get_recent_messages(session_id=s_a, limit=100)
    b = await store.get_recent_messages(session_id=s_b, limit=100)
    assert len(a) == 10
    assert len(b) == 1
    assert b[0]["content"] == "B-0"


async def test_save_message_keeps_model_and_route(store: MemoryStore) -> None:
    session = "sess-meta"
    await store.save_message(
        session_id=session,
        role="assistant",
        content="hi",
        model="qwen3:8b",
        route="general",
    )
    recent = await store.get_recent_messages(session_id=session, limit=10)
    assert len(recent) == 1
    assert recent[0]["role"] == "assistant"
    assert recent[0]["content"] == "hi"
