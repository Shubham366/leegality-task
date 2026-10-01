from connection_utils.db.session import (
    get_session_context,
    session,
    set_session_context,
)

__all__ = ["get_session_context", "init_db", "session", "set_session_context"]


def init_db() -> None:
    from sqlalchemy import create_engine

    from connection_utils.db.session import DB_PATH
    from models.networks import Base

    sync_engine = create_engine(f"sqlite:///{DB_PATH}")
    try:
        Base.metadata.create_all(bind=sync_engine)
    finally:
        sync_engine.dispose()
