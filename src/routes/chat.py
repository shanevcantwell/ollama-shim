import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from utils import map_ollama_options_to_openai, stream_and_transform_llm_response, check_backend_health, call_llm
from config import LM_STUDIO_BASE_URL, PRIMARY_MODEL_URL

router = APIRouter()

@router.post("/v1/chat/completions")
async def handle_openai_completions(request: Request):
    """Receives an OpenAI-compatible request and forwards it to the LM Studio backend."""
    print(f"--- Received request on: {request.url.path} ---")
    try:
        openai_data = await request.json()
        print(f"--- 1. Received OpenAI Request ---\n{openai_data}")

        # Check backend availability before calling
        if not (await check_backend_health()):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": {
                        "message": "Primary model service unavailable",
                        "code": 503,
                        "suggested_action": "Check LM Studio server at " + LM_STUDIO_BASE_URL
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

@router.post("/api/chat")
async def handle_ollama_chat(request: Request):
    """
    Receives an Ollama-specific chat request, translates it to the OpenAI format,
    and forwards it to the LM Studio backend.
    """
    try:
        ollama_data = await request.json()
        print(f"--- 1. Received Ollama Chat Request ---\n{ollama_data}")

        # Check backend availability before calling
        if not (await check_backend_health()):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": {
                        "message": "Primary model service unavailable",
                        "code": 503,
                        "suggested_action": "Check LM Studio server at " + LM_STUDIO_BASE_URL
                    }
                }
            )

        primary_payload = {
            "model": ollama_data.get("model"),
            "messages": ollama_data.get("messages"),
            "stream": ollama_data.get("stream", False)
        }
        if "options" in ollama_data:
            openai_options = map_ollama_options_to_openai(ollama_data["options"])
            primary_payload.update(openai_options)

        if primary_payload["stream"]:
            return StreamingResponse(stream_and_transform_llm_response(primary_payload), media_type="application/x-ndjson")
        else:
            final_content = ""
            async for chunk in stream_and_transform_llm_response(primary_payload):
                data = json.loads(chunk)
                if not data["done"]:
                    final_content += data["message"]["content"]

            ollama_response = {
                "model": ollama_data.get("model"),
                "message": {
                    "role": "assistant",
                    "content": final_content
                },
                "done": True
            }
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