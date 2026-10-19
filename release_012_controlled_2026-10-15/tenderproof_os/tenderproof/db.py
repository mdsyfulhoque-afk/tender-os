import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DB_PATH, ensure_directories


class Base(DeclarativeBase):
    pass


_ENGINE_CACHE = {}


def get_db_path(db_path: str | Path | None = None) -> Path:
    selected = db_path or os.environ.get("TENDERPROOF_DB_PATH") or DB_PATH
    return Path(selected)


def get_engine(db_path: str | Path | None = None):
    path = get_db_path(db_path)
    ensure_directories()
    path.parent.mkdir(parents=True, exist_ok=True)
    key = str(path.resolve())
    if key not in _ENGINE_CACHE:
        _ENGINE_CACHE[key] = create_engine(
            f"sqlite:///{key}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        @event.listens_for(_ENGINE_CACHE[key], "connect")
        def _foreign_keys(connection, _record):
            connection.execute("PRAGMA foreign_keys=ON")
    return _ENGINE_CACHE[key]


def init_db(db_path: str | Path | None = None) -> Path:
    from . import models  # noqa: F401 - register SQLAlchemy models

    from .migrations import migrate

    path = get_db_path(db_path).resolve()
    engine = get_engine(path)
    migrate(engine, path, Base.metadata)
    return path


def make_session(db_path: str | Path | None = None):
    return sessionmaker(bind=get_engine(db_path), autoflush=False, expire_on_commit=False, future=True)


@contextmanager
def get_session(db_path: str | Path | None = None):
    SessionLocal = make_session(db_path)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

