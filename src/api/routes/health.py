"""Health check route."""

from fastapi import APIRouter
from src.api.schemas.responses import HealthResponse
from src.config.settings import get_settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and version.
    """
    settings = get_settings()
    
    # TODO: Check dependencies (Redis, LLM, etc.)
    dependencies = {
        "redis": "not_configured",  # Will implement in Week 4
        "llm": "not_configured"      # Will implement in Week 3
    }
    
    return HealthResponse(
        status="healthy",
        version=settings.version,
        dependencies=dependencies
    )
