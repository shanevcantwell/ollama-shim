import pytest
from src.utils import translate_ollama_options_to_openai
from src.routes.chat import translate_ollama_messages_to_openai

# --- Unit Tests for src.utils.translate_ollama_options_to_openai ---

def test_translate_options_simple():
    """Tests basic 1:1 option translation."""
    ollama_data = {"model": "test-model", "options": {"temperature": 0.5, "seed": 42}}
    expected = {"model": "test-model", "temperature": 0.5, "seed": 42}
    assert translate_ollama_options_to_openai(ollama_data) == expected

def test_translate_options_renamed():
    """Tests renamed options like num_predict -> max_tokens."""
    ollama_data = {"model": "test-model", "options": {"num_predict": 100, "repeat_penalty": 1.2}}
    expected = {"model": "test-model", "max_tokens": 100, "frequency_penalty": 1.2}
    assert translate_ollama_options_to_openai(ollama_data) == expected

def test_translate_options_empty():
    """Tests that it handles empty options."""
    ollama_data = {"model": "test-model", "options": {}}
    expected = {"model": "test-model"}
    assert translate_ollama_options_to_openai(ollama_data) == expected

# --- Unit Tests for src.routes.chat.translate_ollama_messages_to_openai ---

def test_translate_chat_messages_text_only():
    """Tests that text-only messages are passed through unchanged."""
    messages = [{"role": "user", "content": "Hello"}]
    assert translate_ollama_messages_to_openai(messages) == messages

def test_translate_chat_messages_with_image():
    """
    Tests that an Ollama message with an 'images' key is correctly
    transformed into an OpenAI-compatible 'content' array.
    """
    ollama_messages = [
        {
            "role": "user",
            "content": "What's in this image?",
            "images": ["/9j/FAKE_BASE64_STRING..."]
        }
    ]
    
    expected_messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/png;base64,/9j/FAKE_BASE64_STRING..."}
                }
            ]
        }
    ]
    
    assert translate_ollama_messages_to_openai(ollama_messages) == expected_messages

def test_translate_chat_messages_image_only():
    """Tests that a message with *only* an image is translated correctly."""
    ollama_messages = [
        {
            "role": "user",
            "content": "", # Empty content
            "images": ["/9j/FAKE_BASE64_STRING..."]
        }
    ]
    
    expected_messages = [
        {
            "role": "user",
            "content": [
                # No 'text' part should be added if content was empty
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/png;base64,/9j/FAKE_BASE64_STRING..."}
                }
            ]
        }
    ]
    
    assert translate_ollama_messages_to_openai(ollama_messages) == expected_messages