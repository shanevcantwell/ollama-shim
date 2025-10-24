from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/v1/completions")
async def handle_unsupported_completions():
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "message": "This endpoint is not supported. Please use /v1/chat/completions.",
                "code": "unsupported_endpoint",
            }
        },
    )
