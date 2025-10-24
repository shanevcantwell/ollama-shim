import httpx
import asyncio
import json
from datetime import datetime
import re
from fastapi import HTTPException
from config import PRIMARY_MODEL_URL, API_TIMEOUT, RESPONSE_TIMEOUT, LM_STUDIO_BASE_URL

def map_ollama_options_to_openai(ollama_options: dict) -> dict:
    """Maps Ollama-specific options to OpenAI-compatible parameters."""
    openai_params = {}
    if "temperature" in ollama_options:
        openai_params["temperature"] = ollama_options["temperature"]
    if "top_p" in ollama_options:
        openai_params["top_p"] = ollama_options["top_p"]
    if "repeat_penalty" in ollama_options:
        openai_params["frequency_penalty"] = ollama_options["repeat_penalty"]
    if "seed" in ollama_options:
        openai_params["seed"] = ollama_options["seed"]
    if "num_predict" in ollama_options:
        openai_params["max_tokens"] = ollama_options["num_predict"]
    return openai_params

def parse_model_id(model_id: str) -> dict:
    """Parses a model ID to extract parameter size and quantization level."""
    details = {
        "parameter_size": "N/A",
        "quantization_level": "N/A",
    }

    # Look for parameter size like 7b, 13b, 70b
    param_match = re.search(r'(\d+b)', model_id, re.IGNORECASE)
    if param_match:
        details["parameter_size"] = param_match.group(1).upper()

    # Look for quantization level like Q4_K_M, Q5_0
    quant_match = re.search(r'(q\d(_[a-z_]+)?)', model_id, re.IGNORECASE)
    if quant_match:
        details["quantization_level"] = quant_match.group(1).upper()

    return details

async def stream_and_transform_llm_response(payload: dict):
    """Streams response from LLM, transforms it to Ollama format, and yields it."""
    model_name = payload.get("model", "unknown_model")
    try:
        async with httpx.AsyncClient(timeout=RESPONSE_TIMEOUT) as client:
            async with client.stream("POST", PRIMARY_MODEL_URL, json=payload, timeout=API_TIMEOUT) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith('data: '):
                        continue

                    stripped_line = line[6:].strip()
                    if stripped_line == '[DONE]':
                        break

                    try:
                        chunk = json.loads(stripped_line)
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0]['delta']
                            if 'content' in delta:
                                ollama_chunk = {
                                    "model": model_name,
                                    "created_at": datetime.now().isoformat(),
                                    "message": {
                                        "role": "assistant",
                                        "content": delta['content']
                                    },
                                    "done": False
                                }
                                yield json.dumps(ollama_chunk) + '\n'
                    except json.JSONDecodeError:
                        print(f"--- JSONDecodeError in stream chunk: {stripped_line} ---")
                        continue
    except (httpx.RequestError, httpx.HTTPStatusError, asyncio.TimeoutError) as e:
        error_msg = f"Failed to connect to {PRIMARY_MODEL_URL}: {type(e).__name__} - {e}"
        print(f"--- Error during streaming ---\n{error_msg}")

    # Send final done message
    final_chunk = {
        "model": model_name,
        "created_at": datetime.now().isoformat(),
        "message": {
            "role": "assistant",
            "content": ""
        },
        "done": True
    }
    yield json.dumps(final_chunk) + '\n'

async def call_llm(url: str, payload: dict):
    """Helper function to make a call to an LLM endpoint."""
    try:
        async with httpx.AsyncClient(timeout=RESPONSE_TIMEOUT) as client:
            response = await asyncio.wait_for(client.post(url, json=payload), timeout=API_TIMEOUT)
            response.raise_for_status()
            return response.json()
    except (httpx.RequestError, httpx.HTTPStatusError, asyncio.TimeoutError) as e:
        error_msg = f"Failed to connect to {url}: {type(e).__name__} - {e}"
        print(f"--- Error calling LLM endpoint --- \n{error_msg}")
        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "message": "Backend service unavailable",
                    "code": 502,
                    "details": error_msg
                }
            }
        ) from e

async def check_backend_health():
    """Check if the primary model endpoint is available"""
    try:
        models_url = f"{LM_STUDIO_BASE_URL.rstrip('/')}/v1/models"
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            await asyncio.wait_for(client.get(models_url), timeout=API_TIMEOUT)
        return True
    except (httpx.RequestError, asyncio.TimeoutError):
        return False
