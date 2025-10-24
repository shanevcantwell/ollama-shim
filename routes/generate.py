import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from utils import map_ollama_options_to_openai, stream_and_transform_llm_response, check_backend_health
from config import LM_STUDIO_BASE_URL

router = APIRouter()

@router.post("/api/generate")
async def handle_ollama_generate(request: Request):
    """
    Receives an Ollama-specific request, translates it to the OpenAI format,
    and forwards it to the LM Studio backend.
    """
    print(f"--- Received request on: {request.url.path} ---")
    try:
        ollama_data = await request.json()
        print(f"--- 1. Received Ollama Request ---\n{ollama_data}")

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

        user_content = []
        if ollama_data.get("prompt"):
            user_content.append({"type": "text", "text": ollama_data["prompt"]})

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
            "model": ollama_data.get("model"), 
            "messages": messages,
            "stream": True # We always stream from the backend
        }
        if "options" in ollama_data:
            openai_options = map_ollama_options_to_openai(ollama_data["options"])
            primary_payload.update(openai_options)
        
        final_content = ""
        async for chunk in stream_and_transform_llm_response(primary_payload):
            data = json.loads(chunk)
            if not data.get("done", False):
                final_content += data.get("message", {}).get("content", "")

        ollama_response = {
            "model": ollama_data.get("model"),
            "response": final_content,
            "done": True
        }
        
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