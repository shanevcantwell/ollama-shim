# ollama_shim.py
#
# REQUIRED LIBRARIES:
# pip install "fastapi[all]" httpx python-dotenv
#
# HOW TO RUN:
# 1. Stop your real Ollama service (to free up port 11434).
# 2. Run this script: uvicorn ollama_shim:app --host 0.0.0.0 --port 11434

import os
from dotenv import load_dotenv
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import json
import asyncio
from urllib.parse import urlparse, urlunparse
from datetime import datetime

# Load environment variables from .env file if present
load_dotenv()

# --- CONFIGURATION ---
PRIMARY_MODEL_URL = os.getenv("PRIMARY_MODEL_URL", "http://localhost:1234/v1/chat/completions")
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "5.0"))
RESPONSE_TIMEOUT = float(os.getenv("RESPONSE_TIMEOUT", "300.0"))

app = FastAPI()

async def call_llm(url: str, payload: dict):
    """Helper function to make a call to an LLM endpoint."""
    try:
        async with httpx.AsyncClient(timeout=RESPONSE_TIMEOUT) as client:
            response = await asyncio.wait_for(client.post(url, json=payload), timeout=API_TIMEOUT)
            response.raise_for_status()
            return response.json()
    except (httpx.RequestError, httpx.HTTPStatusError, asyncio.TimeoutError) as e:
        error_msg = f"Failed to connect to {url}: {str(e)}"
        print(f"--- Error calling LLM endpoint ---\n{error_msg}")
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
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            await asyncio.wait_for(client.get(PRIMARY_MODEL_URL), timeout=API_TIMEOUT)
        return True
    except (httpx.RequestError, asyncio.TimeoutError):
        return False

# --- DUMMY ENDPOINT FOR OPENAI HEALTH CHECKS ---
@app.get("/")
@app.get("/v1")
@app.get("/v1/")
async def handle_health_check():
    """Handles basic health checks from clients, often used by OpenAI libraries."""
    backend_available = await check_backend_health()
    status = "ok" if backend_available else "degraded"
    return JSONResponse(content={
        "status": status,
        "backend_available": backend_available,
        "primary_model_url": PRIMARY_MODEL_URL
    })

# --- DUMMY ENDPOINT FOR OLLAMA '/api/pull' ---
@app.post("/api/pull")
async def handle_pull():
    """Fakes the 'pull' command from Ollama clients to improve compatibility."""
    print("--- Received /api/pull request. Faking success. ---")
    async def fake_pull_stream():
        yield json.dumps({"status": "pulling digest"}) + "\n"
        await asyncio.sleep(0.1)
        yield json.dumps({"status": "success"}) + "\n"
    return StreamingResponse(fake_pull_stream(), media_type="application/x-ndjson")

# --- ENDPOINT FOR OPENAI-STYLE CHAT REQUESTS ---
@app.post("/v1/completions")
async def handle_unsupported_completions():
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "message": "This endpoint is not supported. Please use /v1/chat/completions.",
                "code": "unsupported_endpoint",
            }
        },
    )

@app.post("/v1/chat/completions")
async def handle_openai_completions(request: Request):
    """Receives an OpenAI-compatible request and forwards it to the LM Studio backend."""
    print(f"--- Received request on: {request.url.path} ---")
    try:
        openai_data = await request.json()
        print(f"--- 1. Received OpenAI Request ---\n{openai_data}\n")

        # Check backend availability before calling
        if not (await check_backend_health()):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": {
                        "message": "Primary model service unavailable",
                        "code": 503,
                        "suggested_action": "Check LM Studio server at " + PRIMARY_MODEL_URL
                    }
                }
            )

        print(f"--- 2a. Forwarding to LM Studio ---")
        lm_studio_response = await call_llm(PRIMARY_MODEL_URL, openai_data)
        print(f"--- 2b. Received from LM Studio ---")
        return JSONResponse(content=lm_studio_response)

    except HTTPException:
        raise
    except Exception as e:
        print(f"An error occurred in /v1/chat/completions: {e}")
        return JSONResponse(status_code=500, content={
            "error": {
                "message": str(e),
                "code": 500,
                "details": f"Ollama Shim service encountered an unexpected error"
            }
        })

# --- ENDPOINT FOR OLLAMA-SPECIFIC '/api/generate' ---
@app.post("/api/chat")
async def handle_ollama_chat(request: Request):
    """
    Receives an Ollama-specific chat request, translates it to the OpenAI format,
    and forwards it to the LM Studio backend.
    """
    try:
        ollama_data = await request.json()
        print(f"--- 1. Received Ollama Chat Request ---\n#{ollama_data}\n")

        # Check backend availability before calling
        if not (await check_backend_health()):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": {
                        "message": "Primary model service unavailable",
                        "code": 503,
                        "suggested_action": "Check LM Studio server at " + PRIMARY_MODEL_URL
                    }
                }
            )

        primary_payload = {
            "model": ollama_data.get("model"), "messages": ollama_data.get("messages")
        }
        
        print(f"--- 2a. Forwarding to Primary Model ---")
        primary_response_json = await call_llm(PRIMARY_MODEL_URL, primary_payload)
        final_content = primary_response_json["choices"][0]["message"]["content"]

        ollama_response = {
            "model": ollama_data.get("model"),
            "message": {
                "role": "assistant",
                "content": final_content
            },
            "done": True
        }
        
        print(f"--- 4. Responding to Client ---\n{ollama_response}\n")
        return JSONResponse(content=ollama_response)

    except HTTPException:
        raise
    except Exception as e:
        print(f"An error occurred in /api/chat: {e}")
        return JSONResponse(status_code=500, content={
            "error": {
                "message": str(e),
                "code": 500,
                "details": f"Ollama Shim service encountered an unexpected error"
            }
        })

@app.post("/api/generate")
async def handle_ollama_generate(request: Request):
    """
    Receives an Ollama-specific request, translates it to the OpenAI format,
    and forwards it to the LM Studio backend.
    """
    print(f"--- Received request on: {request.url.path} ---")
    try:
        ollama_data = await request.json()
        print(f"--- 1. Received Ollama Request ---\n#{ollama_data}\n")

        # Check backend availability before calling
        if not (await check_backend_health()):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": {
                        "message": "Primary model service unavailable",
                        "code": 503,
                        "suggested_action": "Check LM Studio server at " + PRIMARY_MODEL_URL
                    }
                }
            )

        user_content = []

        if ollama_data.get("images"):
            for img_b64 in ollama_data["images"]:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                })
        
        messages = [{"role": "user", "content": user_content}]
        if ollama_data.get("system"):
            messages.insert(0, {"role": "system", "content": ollama_data["system"]})
        
        primary_payload = {
            "model": ollama_data.get("model"), "messages": messages
        }
        
        print(f"--- 2a. Forwarding to Primary Model ---")
        primary_response_json = await call_llm(PRIMARY_MODEL_URL, primary_payload)
        final_content = primary_response_json["choices"][0]["message"]["content"]

        ollama_response = {
            "model": ollama_data.get("model"),
            "response": final_content,
            "done": True
        }
        
        print(f"--- 4. Responding to Client ---\n{ollama_response}\n")
        return JSONResponse(content=ollama_response)

    except HTTPException:
        raise
    except Exception as e:
        print(f"An error occurred in /api/generate: {e}")
        return JSONResponse(status_code=500, content={
            "error": {
                "message": str(e),
                "code": 500,
                "details": f"Ollama Shim service encountered an unexpected error"
            }
        })

# --- ENDPOINT FOR OLLAMA-SPECIFIC '/api/tags' ---
@app.post("/api/show")
async def handle_ollama_show(request: Request):
    """Returns dummy information about a model to satisfy client requests."""
    try:
        ollama_data = await request.json()
        model_name = ollama_data.get("name")
        print(f"--- Received /api/show request for model: {model_name} ---")

        # Return a dummy response, as we don't have detailed model info.
        response_data = {
            "license": "",
            "modelfile": "# Modelfile generated by Ollama Shim",
            "parameters": "",
            "template": "",
            "details": {
                "family": "",
                "format": "gguf",
                "parameter_size": "",
                "quantization_level": ""
            }
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        print(f"An error occurred in /api/show: {e}")
        return JSONResponse(status_code=500, content={
            "error": {
                "message": str(e),
                "code": 500,
                "details": f"Ollama Shim service encountered an unexpected error"
            }
        })

@app.get("/api/tags")
async def handle_tags():
    """
    Fetches the list of available models from the LM Studio backend and
    translates it to the Ollama-compatible format.
    """
    print("--- Received /api/tags request. Checking LM Studio for models. ---")

    try:
        # Check backend availability before calling
        if not (await check_backend_health()):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": {
                        "message": "Model service unavailable",
                        "code": 503,
                        "suggested_action": "Check LM Studio server at " + PRIMARY_MODEL_URL
                    }
                }
            )

        # Construct the /v1/models URL from the PRIMARY_MODEL_URL
        parsed_url = urlparse(PRIMARY_MODEL_URL)
        models_url = urlunparse((parsed_url.scheme, parsed_url.netloc, "/v1/models", "", "", ""))

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await asyncio.wait_for(client.get(models_url), timeout=API_TIMEOUT)
            response.raise_for_status()
            lm_studio_models_data = response.json()

        # Transform the OpenAI-style response to Ollama-style
        ollama_models = []
        for model in lm_studio_models_data.get("data", []):
            model_id = model.get("id")
            if model_id:
                modified_time = datetime.fromtimestamp(model.get("created", 0)).isoformat() + "Z"
                family = model_id.split('-')[0] if '-' in model_id else model_id

                ollama_models.append({
                    "name": model_id,
                    "model": model_id,
                    "modified_at": modified_time,
                    "size": 0,  # Size info is not available from LM Studio's API
                    "digest": model.get("id"),  # Use ID as a fake digest
                    "details": {
                        "format": "gguf",
                        "family": family,
                        "families": [family],
                        "parameter_size": "N/A",
                        "quantization_level": "N/A"
                    }
                })

        response_data = {"models": ollama_models}
        print(f"--- Responding to /api/tags with {len(ollama_models)} model(s). ---")
        return JSONResponse(content=response_data)

    except HTTPException:
        raise
    except (httpx.RequestError, asyncio.TimeoutError) as e:
        error_msg = f"Failed to connect to model service at {models_url}: {str(e)}"
        print(error_msg)
        return JSONResponse(
            status_code=502,
            content={
                "error": {
                    "message": "Model service unavailable",
                    "code": 502,
                    "details": error_msg
                }
            }
        )
    except Exception as e:
        print(f"An error occurred in /api/tags: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": str(e),
                    "code": 500,
                    "details": f"Ollama Shim service encountered an unexpected error"
                }
            }
        )

# Add startup health check endpoint
@app.get("/health")
async def health_check():
    """Provides a detailed health check of the shim and its backend connection."""
    backend_available = await check_backend_health()
    return JSONResponse(content={
        "status": "ok",
        "backend_available": backend_available,
        "primary_model_url": PRIMARY_MODEL_URL,
        "api_timeout_seconds": API_TIMEOUT,
        "response_timeout_seconds": RESPONSE_TIMEOUT
    })