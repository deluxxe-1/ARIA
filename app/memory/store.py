from pathlib import Path

import aiosqlite


class MemoryStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def _init_db(self) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    model TEXT,
                    route TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_session_id_id
                ON messages(session_id, id DESC)
                """
            )
            await conn.commit()

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model: str | None = None,
        route: str | None = None,
    ) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO messages (session_id, role, content, model, route)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, role, content, model, route),
            )
            await conn.commit()

    async def get_recent_messages(self, session_id: str, limit: int = 12) -> list[dict[str, str]]:
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute(
                """
                SELECT role, content
                FROM messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ) as cursor:
                rows = await cursor.fetchall()

        return [
            {"role": row[0], "content": row[1]}
            for row in reversed(rows)
        ]
