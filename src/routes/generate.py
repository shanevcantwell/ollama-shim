# src/routes/generate.py

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import json

# Use relative imports to get the *shared* helper functions
from ..utils import (
    logger, client, translate_ollama_options_to_openai, 
    stream_translator, get_iso_timestamp, get_chat_completions_url
)

router = APIRouter()

@router.post("/api/generate")
async def handle_ollama_generate(request: Request):
    try:
        ollama_data = await request.json()

        logger.info(f"Received /api/generate request for model: {ollama_data.get('model')}")
        logger.debug(f"Full /api/generate payload: {json.dumps(ollama_data)}")

        openai_payload = translate_ollama_options_to_openai(ollama_data)
        
        user_content = []
        if ollama_data.get("prompt"):
            user_content.append({"type": "text", "text": ollama_data["prompt"]})
        if ollama_data.get("images"):
            logger.info(f"Translating {len(ollama_data['images'])} image(s) for LM Studio.")
            for img_b64 in ollama_data["images"]:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                })
        
        messages = [{"role": "user", "content": user_content}]
        if ollama_data.get("system"):
            messages.insert(0, {"role": "system", "content": ollama_data["system"]})
        openai_payload["messages"] = messages
        
        is_streaming_request = ollama_data.get("stream", False)
        openai_payload["stream"] = is_streaming_request

        # --- THIS IS THE FIX ---
        # This function gets the URL from your .env file via config.py
        chat_url = get_chat_completions_url()
        # ---

        # --- BRANCH 1: Streaming ---
        if is_streaming_request:
            logger.info(f"Forwarding as STREAMING request to {chat_url}...")
            
            lm_studio_stream_context = client.stream("POST", chat_url, json=openai_payload)
            lm_studio_stream_response = await lm_studio_stream_context.__aenter__()
            
            lm_studio_stream_response.raise_for_status()
            
            return StreamingResponse(
                stream_translator(
                    lm_studio_stream_response, 
                    response_format="generate",
                    model_name=openai_payload["model"],
                    context_to_close=lm_studio_stream_context
                ),
                media_type="application/x-ndjson"
            )

        # --- BRANCH 2: Non-Streaming ---
        else:
            logger.info(f"Forwarding as NON-STREAMING request to {chat_url}...")
            response = await client.post(chat_url, json=openai_payload)
            response.raise_for_status()
            openai_json = response.json()
            
            logger.debug(f"Received non-streaming response from LM Studio: {openai_json}")

            final_content = openai_json["choices"][0]["message"]["content"]
            
            ollama_response = {
                "model": openai_json["model"],
                "created_at": get_iso_timestamp(),
                "response": final_content,
                "done": True,
                "context": [],
            }
            if "usage" in openai_json and openai_json["usage"]:
                 ollama_response.update({
                    "total_duration": openai_json["usage"].get("total_duration_sec", 0) * 1_000_000_000,
                    "prompt_eval_count": openai_json["usage"]["prompt_tokens"],
                    "eval_count": openai_json["usage"]["completion_tokens"],
                 })

            logger.info("Returning non-streaming response to client.")
            logger.debug(f"Full non-streaming response: {ollama_response}")
            return JSONResponse(content=ollama_response)

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred in /api/generate: {e.response.text}", exc_info=True)
        return JSONResponse(status_code=e.response.status_code, content={"error": str(e.response.text)})
    
    # --- THIS IS THE BLOCK THAT CATCHES THE "Failed to connect..." ERROR ---
    except httpx.ConnectError as e:
        error_message = f"Failed to connect to LM Studio at {chat_url}: {e}"
        logger.error(error_message, exc_info=True)
        # This creates the 502 error payload you're seeing
        return JSONResponse(status_code=502, content={"detail": {"error": {"message": "Backend service unavailable", "code": 502, "details": str(e)}}})
    
    except Exception as e:
        logger.error(f"An error occurred in /api/generate: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})