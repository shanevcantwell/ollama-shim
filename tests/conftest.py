import pytest
from fastapi.testclient import TestClient
from ..main import app  # Changed from '.main' to '..main'

@pytest.fixture(scope="module")
def test_client():
    client = TestClient(app)
    yield client
