from collections.abc import Iterator
from datetime import date

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def make_engine(url: str) -> Engine:
    # Small pool with pre-ping: a serverless instance can sit idle long enough for the
    # database to drop its connection. Prepared statements are off for PgBouncer-style
    # poolers (Neon's pooled endpoint), which do not support them.
    return create_engine(
        url,
        pool_size=3,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"prepare_threshold": None},
    )


def get_db(request: Request) -> Iterator[Session]:
    """One session per request; rolled back if the request fails."""
    session: Session = request.app.state.session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_today(request: Request) -> date:
    """The app's notion of 'today'. Tests replace the clock to stay deterministic."""
    return request.app.state.clock()


def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
