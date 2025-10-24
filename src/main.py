# src/main.py

import uvicorn
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

# --- THIS IS THE FIX ---
# Use relative imports
from .config import settings
from .utils import startup_client, shutdown_client
from .routes import health, ollama_compat, chat, generate, unsupported

# --- Logging Configuration ---
logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger("uvicorn.error")
logger.setLevel(settings.LOG_LEVEL.upper())


# --- App Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_client()
    yield
    await shutdown_client()

# --- Create FastAPI App ---
app = FastAPI(
    title="Ollama to LM Studio Shim",
    description="Translates Ollama API requests to an OpenAI-compatible API (like LM Studio) and back.",
    version="1.0.0",
    lifespan=lifespan
)

# --- Include Routers ---
logger.info("Including routers...")
app.include_router(health.router, tags=["Health"])
app.include_router(ollama_compat.router, tags=["Ollama Compatibility"])
app.include_router(chat.router, tags=["Ollama API"])
app.include_router(generate.router, tags=["Ollama API"])
app.include_router(unsupported.router, tags=["Unsupported"])


# --- Run with Uvicorn ---
if __name__ == "__main__":
    """
    This block allows you to run the app directly for testing:
    python -m src.main
    
    Your run.sh script uses:
    python -m uvicorn src.main:app --host 0.0.0.0 --port 11434
    """
    logger.info("Starting Uvicorn server directly for development...")
    uvicorn.run(
        "src.main:app", # Run from the 'src' module
        host="0.0.0.0",
        port=11434,
        log_level=settings.LOG_LEVEL.lower(),
        reload=True
    )
