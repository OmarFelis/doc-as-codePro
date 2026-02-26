"""FastAPI application for doc-as-code service."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.routes import analysis, health
from src.config.settings import get_settings
from src.utils.logging import setup_logging, get_logger

# Setup logging
setup_logging(debug=False)  # Production mode
logger = get_logger(__name__)

# Get settings
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("api_startup", service=settings.service_name, version=settings.version, environment=settings.environment)
    yield
    logger.info("api_shutdown", service=settings.service_name)


# Create FastAPI app
app = FastAPI(
    title="Doc-as-Code API",
    description="API para análisis de código y generación automática de documentación",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure from settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics", tags=["Metrics"])

# Include routers
app.include_router(health.router, prefix="", tags=["Health"])
app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])



@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "version": settings.version,
        "docs_url": "/docs",
        "health_url": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
