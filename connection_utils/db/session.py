from contextvars import ContextVar, Token
from pathlib import Path
from typing import Union

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)

DB_PATH = Path(__file__).resolve().parent / "db.sqlite3"

engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}")


@event.listens_for(engine.sync_engine, "connect")
def _enable_foreign_keys(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

session_context: ContextVar[int] = ContextVar("session_context")


def get_session_context() -> int:
    return session_context.get()


def set_session_context(session_id: int) -> Token:
    return session_context.set(session_id)


session: Union[AsyncSession, async_scoped_session] = async_scoped_session(
    session_factory=async_session_factory,
    scopefunc=get_session_context,
)
