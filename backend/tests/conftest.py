import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    database_path = tmp_path / "test.db"
    settings = Settings(
        app_env="test",
        database_url=f"sqlite:///{database_path.as_posix()}",
        llm_provider="fake",
    )
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
