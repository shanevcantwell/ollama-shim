# Save this file as: ollama_shim_mitm.py
#
# REQUIRED LIBRARIES:
# pip install "fastapi[all]" httpx
#
# HOW TO RUN:
# 1. Stop your real Ollama service (to free up port 11434).
# 2. Start LM Studio server(s) with your primary and refiner models.
# 3. Run this script: uvicorn ollama_shim_mitm:app --host 0.0.0.0 --port 11434

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json

# --- CONFIGURATION ---
PRIMARY_MODEL_URL = "http://localhost:1234/v1/chat/completions"
# Define the endpoint for your second (refiner) model.
# This could be another LM Studio instance on a different port or a different API.
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

@app.post("/api/generate")
async def handle_generate(request: Request):
    """
    Receives an Ollama request, gets content from a primary model,
    refines it with a secondary model, and returns the result.
    """
    try:
        ollama_data = await request.json()
        print(f"--- 1. Received Ollama Request ---\n{ollama_data}\n")

        # --- 2. Translate and Send to Primary Model for Content ---
        messages = [{"role": "user", "content": ollama_data.get("prompt", "")}]
        if ollama_data.get("system"):
            messages.insert(0, {"role": "system", "content": ollama_data["system"]})
        
        primary_payload = {
            "model": "primary-model",
            "messages": messages
        }
        
        print(f"--- 2a. Forwarding to Primary Model ---")
        primary_response_json = await call_llm(PRIMARY_MODEL_URL, primary_payload)
        raw_content = primary_response_json["choices"][0]["message"]["content"]
        print(f"--- 2b. Received Raw Content ---\n{raw_content}\n")

        # --- 3. Send Raw Content to Refiner Model for Formatting ---
        # The MitM step: if the original request asks for JSON output.
        if ollama_data.get("format") == "json":
            print(f"--- 3a. Forwarding to Refiner Model for JSON formatting ---")
            refiner_payload = {
                "model": "refiner-model",
                "messages": [
                    {"role": "system", "content": REFINER_SYSTEM_PROMPT},
                    {"role": "user", "content": raw_content}
                ],
                "temperature": 0.0 # We want deterministic formatting
            }
            refiner_response_json = await call_llm(REFINER_MODEL_URL, refiner_payload)
            final_content = refiner_response_json["choices"][0]["message"]["content"]
            print(f"--- 3b. Received Refined JSON ---\n{final_content}\n")
        else:
            final_content = raw_content # Skip refinement if not a JSON request

        # --- 4. Translate Final Content back to Ollama Format ---
        ollama_response = {
            "model": ollama_data.get("model"),
            "response": final_content,
            "done": True,
        }
        
        print(f"--- 4. Responding to Client ---\n{ollama_response}\n")
        return JSONResponse(content=ollama_response)

    except Exception as e:
        print(f"An error occurred: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/tags")
async def handle_tags():
    return JSONResponse(content={"models": []})