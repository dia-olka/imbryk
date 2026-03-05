"""Shared test fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from ingestion_api.categoriser import StubCategoriser
from ingestion_api.database import Base, get_db
from ingestion_api.main import app, limiter, set_categoriser


@pytest.fixture()
def db_engine():
    """In-memory SQLite engine shared across threads."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(db_engine):
    """Database session for testing."""
    session_factory = sessionmaker(bind=db_engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def stub_categoriser():
    """StubCategoriser returning geopolitics-and-diplomacy + domestic-politics-and-policy."""
    return StubCategoriser(categories=["geopolitics-and-diplomacy", "domestic-politics-and-policy"])


@pytest.fixture()
def client(db_session, stub_categoriser):
    """TestClient wired to in-memory DB and stub categoriser."""
    set_categoriser(stub_categoriser)

    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    # Disable rate limiting for tests
    limiter.enabled = False
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    limiter.enabled = True
