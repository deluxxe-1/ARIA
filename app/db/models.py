from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Index, func


class Base(DeclarativeBase):
    pass


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(index=False)
    role: Mapped[str]
    content: Mapped[str]
    model: Mapped[str | None]
    route: Mapped[str | None]
    created_at: Mapped[str] = mapped_column(server_default=func.current_timestamp())

    __table_args__ = (
        Index(
            "idx_messages_session_id_id",
            "session_id",
            "id",
            postgresql_using=None,
            sqlite_where=None,
        ),
    )
