import asyncio
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.db.migrations import run_upgrade_head, stamp_head_if_needed
from app.db.models import Message
from app.db.session import build_engine, build_session_factory


class MemoryStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._engine = build_engine(self.db_path)
        self._session_factory = build_session_factory(self._engine)

    async def _init_db(self) -> None:
        await asyncio.to_thread(stamp_head_if_needed, self.db_path)
        await run_upgrade_head(db_path=self.db_path)

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model: str | None = None,
        route: str | None = None,
    ) -> None:
        msg = Message(
            session_id=session_id,
            role=role,
            content=content,
            model=model,
            route=route,
        )
        async with self._session_factory() as session:
            session.add(msg)
            await session.commit()

    async def get_recent_messages(
        self,
        session_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(Message)
            .filter_by(session_id=session_id)
            .order_by(Message.id.desc())
            .limit(limit)
        )
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            rows = result.scalars().all()

        return [
            {
                "role": m.role,
                "content": m.content,
                "model": m.model,
                "route": m.route,
            }
            for m in reversed(rows)
        ]
