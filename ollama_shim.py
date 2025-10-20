# Save this file as: ollama_shim.py
#
# REQUIRED LIBRARIES:
# pip install "fastapi[all]" httpx
#
# HOW TO RUN:
# 1. Stop your real Ollama service (to free up port 11434).
# 2. Start LM Studio server(s) with your primary and refiner models.
# 3. Run this script: uvicorn ollama_shim:app --host 0.0.0.0 --port 11434

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import json
import asyncio

# --- CONFIGURATION ---
PRIMARY_MODEL_URL = "http://localhost:1234/v1/chat/completions"
REFINER_MODEL_URL = "http://localhost:1234/v1/chat/completions"

REFINER_SYSTEM_PROMPT = """
You are a JSON formatting expert. Your only task is to take the user's input
and ensure it is a single, valid, minified JSON object.
Do not add any conversational text, explanations, or markdown.
Your entire response must start with `{` and end with `}`.
"""

app = FastAPI()

async def call_llm(url: str, payload: dict):
    """Helper function to make a call to an LLM endpoint."""
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

# --- DUMMY ENDPOINT FOR OPENAI HEALTH CHECKS ---
@app.get("/")
@app.get("/v1")
@app.get("/v1/")
async def handle_health_check():
    print("--- Received OpenAI Health Check. Responding OK. ---")
    return JSONResponse(content={"status": "ok"})

# --- DUMMY ENDPOINT FOR OLLAMA '/api/pull' ---
@app.post("/api/pull")
async def handle_pull():
    print("--- Received /api/pull request. Faking success. ---")
    async def fake_pull_stream():
        yield json.dumps({"status": "pulling digest"}) + "\n"
        await asyncio.sleep(0.1)
        yield json.dumps({"status": "success"}) + "\n"
    return StreamingResponse(fake_pull_stream(), media_type="application/x-ndjson")

# --- ENDPOINT FOR OPENAI-STYLE CHAT REQUESTS ---
@app.post("/v1/chat/completions")
async def handle_openai_completions(request: Request):
    try:
        openai_data = await request.json()
        print(f"--- 1. Received OpenAI Request ---\n{openai_data}\n")
        print(f"--- 2a. Forwarding to LM Studio ---")
        lm_studio_response = await call_llm(PRIMARY_MODEL_URL, openai_data)
        print(f"--- 2b. Received from LM Studio ---\n{lm_studio_response}\n")
        return JSONResponse(content=lm_studio_response)
    except Exception as e:
        print(f"An error occurred in /v1/chat/completions: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- ENDPOINT FOR OLLAMA-SPECIFIC '/api/generate' ---
@app.post("/api/generate")
async def handle_ollama_generate(request: Request):
    """
    Receives an Ollama generate request.
    (This is for the 'nodes.py' file we first looked at)
    """
    try:
        ollama_data = await request.json()
        print(f"--- 1. Received Ollama Request ---\n{ollama_data}\n")
        
        # --- FIX IS HERE: Correctly build the multimodal message ---
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
        # --- END OF FIX ---
        
        primary_payload = {
            "model": ollama_data.get("model"), "messages": messages
        }
        
        print(f"--- 2a. Forwarding to Primary Model ---")
        primary_response_json = await call_llm(PRIMARY_MODEL_URL, primary_payload)
        raw_content = primary_response_json["choices"][0]["message"]["content"]
        
        # ... (Refiner logic) ...
        final_content = raw_content

        ollama_response = {
            "model": ollama_data.get("model"), "response": final_content, "done": True,
        }
        
        print(f"--- 4. Responding to Client ---\n{ollama_response}\n")
        return JSONResponse(content=ollama_response)
    except Exception as e:
        print(f"An error occurred in /api/generate: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- ENDPOINT FOR OLLAMA-SPECIFIC '/api/tags' ---
@app.get("/api/tags")
async def handle_tags():
    print("--- Received /api/tags request. Returning empty list. ---")
    return JSONResponse(content={"models": []})