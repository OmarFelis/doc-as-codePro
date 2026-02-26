"""Session factory para SQLAlchemy."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.config.settings import get_settings


def get_engine(url: str | None = None):
    db_url = url or get_settings().database.url
    return create_engine(db_url, pool_pre_ping=True)


def get_session_factory(url: str | None = None):
    return sessionmaker(bind=get_engine(url), expire_on_commit=False)


def get_session(url: str | None = None) -> Session:
    factory = get_session_factory(url)
    return factory()
