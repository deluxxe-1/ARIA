import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config


def _build_config(
    db_path: Path | None = None,
    sqlalchemy_url: str | None = None,
) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", "alembic")
    cfg.set_main_option("prepend_sys_path", ".")
    if sqlalchemy_url is not None:
        url = sqlalchemy_url
    elif db_path is not None:
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite+aiosqlite:///{db_path.resolve().as_posix()}"
    else:
        raise ValueError("Either db_path or sqlalchemy_url must be provided")
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def _table_exists_sync(db_path: Path, table_name: str) -> bool:
    import sqlite3

    try:
        conn = sqlite3.connect(str(db_path))
        try:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            row = cur.fetchone()
            return row is not None
        finally:
            conn.close()
    except sqlite3.OperationalError:
        return False


def stamp_head_if_needed(db_path: Path) -> None:
    if not db_path.exists():
        return
    has_alembic = _table_exists_sync(db_path, "alembic_version")
    has_messages = _table_exists_sync(db_path, "messages")
    if has_alembic:
        return
    if not has_messages:
        return
    cfg = _build_config(db_path=db_path)
    command.stamp(cfg, "head")


def run_upgrade_head_sync(
    db_path: Path | None = None,
    sqlalchemy_url: str | None = None,
) -> None:
    cfg = _build_config(db_path=db_path, sqlalchemy_url=sqlalchemy_url)
    command.upgrade(cfg, "head")


async def run_upgrade_head(
    db_path: Path | None = None,
    sqlalchemy_url: str | None = None,
) -> None:
    await asyncio.to_thread(
        run_upgrade_head_sync,
        db_path,
        sqlalchemy_url,
    )
