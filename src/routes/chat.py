# src/routes/chat.py

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import json

from ..utils import (
    logger, client, translate_ollama_options_to_openai, 
    stream_translator, get_iso_timestamp, get_chat_completions_url
)

router = APIRouter()

def translate_ollama_messages_to_openai(messages: list) -> list:
    """
    Translates the 'messages' array from Ollama's /api/chat format
    (which uses a top-level 'images' key) to the OpenAI format
    (which uses a 'content' array).
    """
    openai_messages = []
    for msg in messages:
        # If there are no images, just append the message as-is
        if not msg.get("images"):
            openai_messages.append(msg)
            continue
        
        # --- This is the translation logic ---
        # An image is present, so we must build the 'content' array
        
        logger.info(f"Translating {len(msg['images'])} image(s) for role '{msg.get('role')}'")
        
        content_list = []
        
        # 1. Add the text part
        if msg.get("content"):
            content_list.append({
                "type": "text",
                "text": msg["content"]
            })
            
        # 2. Add all the image parts
        for img_b64 in msg["images"]:
            content_list.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"}
            })
            
        # 3. Create the new message object
        openai_messages.append({
            "role": msg.get("role"),
            "content": content_list
        })
        
    return openai_messages


@router.post("/api/chat")
async def handle_ollama_chat(request: Request):
    try:
        ollama_data = await request.json()
        
        logger.info(f"Received /api/chat request for model: {ollama_data.get('model')}")
        logger.debug(f"Full /api/chat payload: {json.dumps(ollama_data)}")

        openai_payload = translate_ollama_options_to_openai(ollama_data)
        
        # --- THIS IS THE FIX ---
        # Translate the messages array to handle images
        ollama_messages = ollama_data.get("messages", [])
        openai_payload["messages"] = translate_ollama_messages_to_openai(ollama_messages)
        # ---

        is_streaming_request = ollama_data.get("stream", False)
        openai_payload["stream"] = is_streaming_request
        
        chat_url = get_chat_completions_url()

        # --- BRANCH 1: Streaming ---
        if is_streaming_request:
            logger.info(f"Forwarding as STREAMING request to {chat_url}...")
            
            lm_studio_stream_context = client.stream("POST", chat_url, json=openai_payload)
            lm_studio_stream_response = await lm_studio_stream_context.__aenter__()
            
            lm_studio_stream_response.raise_for_status()
            
            return StreamingResponse(
                stream_translator(
                    lm_studio_stream_response, 
                    response_format="chat",
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

            ollama_response = {
                "model": openai_json["model"],
                "created_at": get_iso_timestamp(),
                "message": openai_json["choices"][0]["message"],
                "done": True
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
        logger.error(f"HTTP error occurred in /api/chat: {e.response.text}", exc_info=True)
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        logger.error(f"An error occurred in /api/chat: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})