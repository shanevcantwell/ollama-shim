# tests/conftest.py
import pytest
from fastapi.testclient import TestClient

# Import your main FastAPI app
from src.main import app
from src.utils import get_models_url, get_chat_completions_url

@pytest.fixture(scope="function")
def test_client():
    """Provides a synchronous TestClient for the shim app."""
    # TestClient automatically handles the app lifespan (startup/shutdown)
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="function")
def mock_lm_studio_urls():
    """Provides the URLs the app will try to call."""
    return {
        "models_url": get_models_url(),
        "chat_url": get_chat_completions_url()
    }