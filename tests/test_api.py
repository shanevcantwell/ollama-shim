# tests/test_api.py

import pytest
import json
import respx # Import respx
from httpx import Response, ConnectError
# No need to import TestClient here, it comes from the fixture

# --- Sample Payloads (Unchanged) ---
MOCK_LM_STUDIO_MODELS = { "data": [{"id": "mistralai/magistral-small-2509", "created": 1720000000, "object": "model", "owned_by": "unknown"}]}
MOCK_LM_STUDIO_CHAT_RESPONSE = {"id": "chatcmpl-123", "object": "chat.completion", "created": 1720000001, "model": "mistralai/magistral-small-2509", "choices": [{"index": 0, "message": {"role": "assistant", "content": "There are two dogs in the image."}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}}
MOCK_LM_STUDIO_STREAM_CHUNKS = ['data: {"id":"1","choices":[{"delta":{"role":"assistant"}}]}\n\n', 'data: {"id":"2","choices":[{"delta":{"content":"There are"}}]}\n\n', 'data: {"id":"3","choices":[{"delta":{"content":" two dogs."}}]}\n\n', 'data: {"id":"4","choices":[{"delta":{},"finish_reason":"stop"}]}\n\n', 'data: [DONE]\n\n']

# --- The Tests (Using manual 'with respx.mock') ---

def test_health_check(test_client): # No mocking needed
    """Tests the root GET / health check."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.text == '"Ollama is running"'

# --- THIS IS THE FIX ---
# Apply respx context manually
def test_get_tags_success(test_client, mock_lm_studio_urls):
    """Tests the ComfyUI /api/tags endpoint."""
    models_url = mock_lm_studio_urls["models_url"]
    
    with respx.mock as mocker: # Activate mocking
        mocker.get(models_url).return_value(Response(status_code=200, json=MOCK_LM_STUDIO_MODELS))
        
        # Make the call *within* the mock context
        response = test_client.get("/api/tags") 
    
    # Assertions outside the context are fine
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) == 1
    assert data["models"][0]["name"] == "mistralai/magistral-small-2509"

# --- THIS IS THE FIX ---
# Apply respx context manually
def test_get_tags_connection_error(test_client, mock_lm_studio_urls):
    """Tests /api/tags when LM Studio is unreachable."""
    models_url = mock_lm_studio_urls["models_url"]
    
    with respx.mock as mocker:
        mocker.get(models_url).side_effect = ConnectError("Connection failed")
        response = test_client.get("/api/tags")
        
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert "Cannot connect to LM Studio" in data["error"]

# --- THIS IS THE FIX ---
# Apply respx context manually
def test_chat_non_streaming_image(test_client, mock_lm_studio_urls):
    """Tests the AnythingLLM non-streaming image case (/api/chat)."""
    chat_url = mock_lm_studio_urls["chat_url"]
    
    with respx.mock as mocker:
        mock_route = mocker.post(chat_url).return_value(
            Response(status_code=200, json=MOCK_LM_STUDIO_CHAT_RESPONSE)
        )
        
        ollama_payload = {
            "model": "mistralai/magistral-small-2509",
            "stream": False,
            "messages": [{"role": "user", "content": "How many dogs?", "images": ["BINGO_IMG_DATA"]}]
        }
        
        response = test_client.post("/api/chat", json=ollama_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["message"]["content"] == "There are two dogs in the image."
    assert data["done"] is True

    received_payload = json.loads(mock_route.calls[0].request.content)
    expected_content = [
        {"type": "text", "text": "How many dogs?"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,BINGO_IMG_DATA"}}
    ]
    assert received_payload["messages"][0]["content"] == expected_content

# --- THIS IS THE FIX ---
# Apply respx context manually
def test_generate_streaming_with_image(test_client, mock_lm_studio_urls):
    """Tests /api/generate with streaming and an image."""
    chat_url = mock_lm_studio_urls["chat_url"]

    with respx.mock as mocker:
        mocker.post(chat_url).return_value(
            Response(status_code=200, content="".join(MOCK_LM_STUDIO_STREAM_CHUNKS))
        )

        ollama_payload = {
            "model": "mistralai/magistral-small-2509",
            "stream": True,
            "prompt": "How many dogs?",
            "images": ["BINGO_IMG_DATA"]
        }
        
        # TestClient's stream context needs to be inside respx context
        with test_client.stream("POST", "/api/generate", json=ollama_payload) as response:
            assert response.status_code == 200
            # Read chunks *inside* the stream context
            response_chunks = [json.loads(line) for line in response.iter_lines() if line]

    # Assertions outside the contexts are fine
    assert len(response_chunks) == 3
    assert response_chunks[0]["response"] == "There are"
    assert response_chunks[1]["response"] == " two dogs."
    assert response_chunks[2]["done"] is True
    assert response_chunks[2]["response"] == "There are two dogs."