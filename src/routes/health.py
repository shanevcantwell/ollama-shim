from fastapi import APIRouter
from fastapi.responses import JSONResponse
from utils import check_backend_health
from config import LM_STUDIO_BASE_URL, PRIMARY_MODEL_URL, API_TIMEOUT, RESPONSE_TIMEOUT

router = APIRouter()

@router.get("/")
@router.get("/v1")
@router.get("/v1/")
async def handle_health_check():
    """Handles basic health checks from clients, often used by OpenAI libraries."""
    backend_available = await check_backend_health()
    status = "ok" if backend_available else "degraded"
    return JSONResponse(content={
        "status": status,
        "backend_available": backend_available,
        "lm_studio_base_url": LM_STUDIO_BASE_URL,
        "primary_model_url": PRIMARY_MODEL_URL
    })

@router.get("/health")
async def health_check():
    """Provides a detailed health check of the shim and its backend connection."""
    backend_available = await check_backend_health()
    return JSONResponse(content={
        "status": "ok",
        "backend_available": backend_available,
        "lm_studio_base_url": LM_STUDIO_BASE_URL,
        "primary_model_url": PRIMARY_MODEL_URL,
        "api_timeout_seconds": API_TIMEOUT,
        "response_timeout_seconds": RESPONSE_TIMEOUT
    })
