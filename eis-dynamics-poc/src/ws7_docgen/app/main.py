"""DocGen Service - Main FastAPI Application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import upload, processing, export

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting {settings.SERVICE_NAME} Service v{settings.SERVICE_VERSION}")
    logger.info(f"AI Provider: {settings.AI_PROVIDER}")
    logger.info(f"Storage: {'Local' if settings.USE_LOCAL_STORAGE else 'Azure Blob'}")
    logger.info(f"Max ZIP Size: {settings.MAX_ZIP_SIZE_MB}MB")
    logger.info(f"Max Files per ZIP: {settings.MAX_FILES_PER_ZIP}")
    logger.info("=" * 60)

    # Create temp directories
    import os
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    os.makedirs(settings.LOCAL_STORAGE_PATH, exist_ok=True)

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME} Service...")


app = FastAPI(
    title="EIS DocGen Service",
    description="Document Generation & Export Service for Claims Processing",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware - use config or allow all if not configured
cors_origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    upload.router,
    prefix="/api/v1/docgen",
    tags=["upload"],
)
app.include_router(
    processing.router,
    prefix="/api/v1/docgen",
    tags=["processing"],
)
app.include_router(
    export.router,
    prefix="/api/v1/docgen",
    tags=["export"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
    }


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
