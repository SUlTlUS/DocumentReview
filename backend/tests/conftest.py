from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings
from app.database import build_engine, get_db
from app.main import app
from app.models import Base
from app.services.rag import rag_registry


@pytest.fixture
def api_client(tmp_path) -> Generator[TestClient, None, None]:
    engine = build_engine(f"sqlite:///{tmp_path / 'api.db'}")
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'api.db'}",
        upload_dir=tmp_path / "uploads",
        llm_provider="mock",
    )
    settings.ensure_directories()

    def override_db() -> Generator[Session, None, None]:
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings
    rag_registry.clear()
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    rag_registry.clear()

