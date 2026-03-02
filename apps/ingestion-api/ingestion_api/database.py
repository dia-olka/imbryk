"""SQLAlchemy engine setup and session dependency."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from ingestion_api.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db(db_engine=None):
    """Create all tables. Used for dev/testing; production uses Alembic."""
    target_engine = db_engine or engine
    Base.metadata.create_all(bind=target_engine)
