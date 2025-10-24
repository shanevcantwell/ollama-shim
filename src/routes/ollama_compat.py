# src/routes/ollama_compat.py

import time
import asyncio
import json
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
from datetime import datetime, timezone

# --- THIS IS THE FIX ---
# Use relative imports to go up to the 'src' directory
from ..utils import logger, client, get_models_url

router = APIRouter()

@router.post("/api/pull")
async def handle_pull(request: Request):
    try:
        request_data = await request.json()
        model_name = request_data.get("name", "unknown model")
        logger.info(f"Received /api/pull request for '{model_name}'. Faking success.")
    except Exception:
        logger.info("Received /api/pull request. Faking success.")

    async def fake_pull_stream():
        yield json.dumps({"status": "pulling digest"}) + "\n"
        await asyncio.sleep(0.01)
        yield json.dumps({"status": "success"}) + "\n"
    
    return StreamingResponse(fake_pull_stream(), media_type="application/x-ndjson")


@router.get("/api/tags")
async def handle_tags():
    logger.info("Received /api/tags request. Forwarding to LM Studio...")
    models_url = get_models_url()
    logger.debug(f"Calling LM Studio for models at: {models_url}")
    
    try:
        lm_studio_response = await client.get(models_url)
        lm_studio_response.raise_for_status() 
        lm_studio_models_data = lm_studio_response.json()

        ollama_models = []
        for model in lm_studio_models_data.get("data", []):
            model_id = model.get("id")
            if model_id:
                modified_time = datetime.fromtimestamp(
                    model.get("created", time.time()), tz=timezone.utc
                ).isoformat().replace('+00:00', 'Z')
                
                family = model_id.split('-')[0] if '-' in model_id else "unknown"

                ollama_models.append({
                    "name": model_id,
                    "model": model_id,
                    "modified_at": modified_time,
                    "size": model.get("size", 0),
                    "digest": model.get("id"),
                    "details": {
                        "format": "gguf",
                        "family": family,
                        "families": [family] if family != "unknown" else None,
                        "parameter_size": "N/A",
                        "quantization_level": "N/A"
                    }
                })

        response_data = {"models": ollama_models}
        logger.info(f"Responding to /api/tags with {len(ollama_models)} model(s).")
        logger.debug(f"Full /api/tags response: {response_data}")
        return JSONResponse(content=response_data)

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from LM Studio server at {models_url}: {e.response.status_code} {e.response.text}", exc_info=True)
        return JSONResponse(content={"error": f"LM Studio server error: {e.response.text}"}, status_code=500)
    except httpx.RequestError as e:
        logger.error(f"Error connecting to LM Studio at {models_url}: {e}", exc_info=True)
        return JSONResponse(content={"error": f"Cannot connect to LM Studio: {e}"}, status_code=500)
    except Exception as e:
        logger.error(f"An error occurred in /api/tags: {e}", exc_info=True)
        return JSONResponse(content={"error": f"Internal server error: {e}"}, status_code=500)
