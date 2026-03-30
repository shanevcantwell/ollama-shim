# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

# Import your main FastAPI app - works in both dev and installed modes
try:
    from ollama_shim.main import app
    from ollama_shim import utils as utils_module
    from ollama_shim.utils import get_models_url, get_chat_completions_url
except ImportError:
    from src.main import app
    from src import utils as utils_module
    from src.utils import get_models_url, get_chat_completions_url


@pytest.fixture(scope="function")
def test_client():
    """Provides a synchronous TestClient for the shim app."""
    # Create a mock httpx.AsyncClient that returns mocked responses
    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock()
    mock_client.post = AsyncMock()
    mock_client.stream = AsyncMock()

    # Patch the client in utils module to use our mock
    with patch.object(utils_module, 'client', mock_client):
        # Also patch startup_client to skip backend connection check
        with patch.object(utils_module, 'startup_client', new_callable=AsyncMock):
            with patch.object(utils_module, 'shutdown_client', new_callable=AsyncMock):
                with TestClient(app) as client:
                    yield client

@pytest.fixture(scope="function")
def mock_backend_urls():
    """Provides the URLs the app will try to call."""
    return {
        "models_url": get_models_url(),
        "chat_url": get_chat_completions_url()
    }