import json
from httpx import Response
from fastapi.testclient import TestClient

# Changed from httpx_mock to pytest-httpx fixture

def test_generate_non_streaming(test_client: TestClient, httpx_mock):  # This will now be provided by pytest-httpx
    # Mock the response from the LM Studio backend
    mock_response_content = r"""
    data: {\"id\": \"chatcmpl-123\", \"object\": \"chat.completion.chunk\", \"created\": 1694268190, \"model\": \"gpt-3.5-turbo-0613\", \"choices\":[{\"index\": 0, \"delta\": {\"content\": \"Hello\"}, \"finish_reason\": null}]}\\n\\
data: [DONE]\\
    """
    httpx_mock.add_response(url="http://127.0.0.1:1234/v1/chat/completions", content=mock_response_content.encode('utf-8'))

    # Make a request to the /api/generate endpoint
    response = test_client.post("/api/generate", json={
        "model": "test-model",
        "prompt": "Hello",
        "stream": False
    })

    # Assert the response
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["model"] == "test-model"
    assert response_json["response"] == "Hello"
    assert response_json["done"] is True

def test_chat_streaming(test_client: TestClient, httpx_mock):  # This will now be provided by pytest-httpx
    # Mock the response from the LM Studio backend
    mock_response_content = r"""
    data: {\"id\": \"chatcmpl-123\", \"object\": \"chat.completion.chunk\", \"created\": 1694268190, \"model\": \"gpt-3.5-turbo-0613\", \"choices\":[{\"index\": 0, \"delta\": {\"content\": \"Hello\"}, \"finish_reason\": null}]}\\n\\
data: {\"id\": \"chatcmpl-123\", \"object\": \"chat.completion.chunk\", \"created\": 1694268190, \"model\": \"gpt-3.5-turbo-0613\", \"choices\":[{\"index\": 0, \"delta\": {\"content\": \" World\"}, \"finish_reason\": null}]}\\n\\
data: [DONE]\\
    """
    httpx_mock.add_response(url="http://127.0.0.1:1234/v1/chat/completions", content=mock_response_content.encode('utf-8'))

    # Make a request to the /api/chat endpoint
    with test_client.stream("POST", "/api/chat", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": True
    }) as response:
        # Assert the response
        assert response.status_code == 200
        
        # Collect the streaming response
        chunks = list(response.iter_lines())
        
        # Assert the content of the chunks
        assert len(chunks) == 3 # Two content chunks and one final done chunk
        
        chunk1 = json.loads(chunks[0])
        assert chunk1["message"]["content"] == "Hello"
        assert chunk1["done"] is False

        chunk2 = json.loads(chunks[1])
        assert chunk2["message"]["content"] == " World"
        assert chunk2["done"] is False

        chunk3 = json.loads(chunks[2])
        assert chunk3["message"]["content"] == ""
        assert chunk3["done"] is True
