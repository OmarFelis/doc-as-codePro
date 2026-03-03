"""Session factory para SQLAlchemy."""
from sqlalchemy import create_engine, text
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


def init_db(url: str | None = None) -> None:
    """Crea schemas code y quality si no existen, luego crea todas las tablas."""
    from src.db.models import Base
    engine = get_engine(url)
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS code"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS quality"))
        conn.commit()
    Base.metadata.create_all(engine)
