# ollama_shim/routes/health.py
from fastapi import APIRouter
from ..utils import logger

router = APIRouter()

@router.get("/")
@router.head("/")
async def handle_root_health_check():
    """
    Handles the root health check.
    Ollama servers respond with "Ollama is running".
    """
    logger.info("Received root health check. Responding OK.")
    return "Ollama is running"
