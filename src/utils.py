# src/utils.py

import logging
import httpx
import json
from datetime import datetime, timezone

# Use relative import for config
from .config import settings

logger = logging.getLogger("uvicorn.error")

# --- URL Helper Functions ---
# (These now correctly use the settings object)
def get_chat_completions_url() -> str:
    """Builds the chat completions URL from the base URL."""
    return f"{settings.LM_STUDIO_BASE_URL.rstrip('/')}/v1/chat/completions"

def get_models_url() -> str:
    """Builds the models URL from the base URL."""
    return f"{settings.LM_STUDIO_BASE_URL.rstrip('/')}/v1/models"

# --- HTTP Client Lifecycle ---
client = httpx.AsyncClient(timeout=300.0)

async def startup_client():
    logger.info(f"Ollama-to-OpenAI Shim starting up...")
    logger.info(f"Forwarding to LM Studio Base URL: {settings.LM_STUDIO_BASE_URL}")
    try:
        # Test connection on startup
        await client.get(get_models_url())
        logger.info("Successfully connected to LM Studio models endpoint.")
    except Exception as e:
        logger.error(f"STARTUP FAILED: Could not connect to LM Studio at {get_models_url()}: {e}")

async def shutdown_client():
    await client.aclose()
    logger.info("Ollama-to-OpenAI Shim shut down.")

# --- Translation Logic ---

def get_iso_timestamp():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def translate_ollama_options_to_openai(ollama_data: dict) -> dict:
    options = ollama_data.get("options", {})
    
    openai_payload = {
        "model": ollama_data.get("model", "default-model")
    }
    
    for key in ["temperature", "top_p", "stop", "seed"]:
        if key in options:
            openai_payload[key] = options[key]
    
    if "num_predict" in options:
        openai_payload["max_tokens"] = options["num_predict"]
    if "repeat_penalty" in options:
        openai_payload["frequency_penalty"] = options["repeat_penalty"]
    if "top_k" in options:
        openai_payload["top_k"] = options["top_k"]

    return openai_payload

# --- Stream Translator (with lifecycle fix) ---
async def stream_translator(lm_studio_stream, response_format: str, model_name: str, context_to_close=None):
    """
    Async generator that translates an OpenAI-style stream into an
    Ollama-style stream (line-delimited JSON).
    
    It now accepts a 'context_to_close' to manually close the stream.
    """
    full_response_content = ""
    usage_data = None
    
    try:
        async for chunk in lm_studio_stream.aiter_bytes():
            chunk_str = chunk.decode('utf-8')
            for line in chunk_str.splitlines():
                if line.startswith("data: "):
                    line = line[6:]
                if line.strip() == "[DONE]":
                    break
                if not line.strip():
                    continue 

                try:
                    openai_chunk = json.loads(line)
                    
                    if openai_chunk.get("usage"):
                        usage_data = openai_chunk["usage"]
                        continue
                        
                    delta = openai_chunk["choices"][0].get("delta", {})
                    content = delta.get("content")

                    if content:
                        full_response_content += content
                        timestamp = get_iso_timestamp()
                        
                        if response_format == "chat":
                            ollama_chunk = {
                                "model": model_name,
                                "created_at": timestamp,
                                "message": {"role": "assistant", "content": content},
                                "done": False
                            }
                        else: # "generate"
                            ollama_chunk = {
                                "model": model_name,
                                "created_at": timestamp,
                                "response": content,
                                "done": False
                            }
                        
                        logger.debug(f"Streaming chunk: {ollama_chunk}")
                        yield json.dumps(ollama_chunk) + "\n"

                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse stream chunk: {line}")
                    continue
        
        timestamp = get_iso_timestamp()
        
        if response_format == "chat":
            final_chunk = {
                "model": model_name,
                "created_at": timestamp,
                "message": {"role": "assistant", "content": ""},
                "done": True
            }
        else: # "generate"
            final_chunk = {
                "model": model_name,
                "created_at": timestamp,
                "response": full_response_content,
                "done": True,
                "context": []
            }
        
        if usage_data:
            final_chunk["total_duration"] = usage_data.get("total_duration_sec", 0) * 1_000_000_000
            final_chunk["prompt_eval_count"] = usage_data.get("prompt_tokens")
            final_chunk["eval_count"] = usage_data.get("completion_tokens")
        
        logger.info("Stream completed. Sending final 'done' chunk.")
        logger.debug(f"Final chunk: {final_chunk}")
        yield json.dumps(final_chunk) + "\n"

    except Exception as e:
        logger.error(f"Stream translation failed: {e}", exc_info=True)
        error_chunk = {
            "error": f"Stream translation failed: {e}",
            "done": True
        }
        yield json.dumps(error_chunk) + "\n"
    finally:
        # Manually close the stream context that was passed in.
        if context_to_close:
            logger.debug("Manually closing stream context.")
            await context_to_close.__aexit__(None, None, None)
        else:
            logger.debug("Aclosing stream object directly.")
            await lm_studio_stream.aclose()