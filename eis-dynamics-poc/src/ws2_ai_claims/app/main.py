"""WS2: AI Claims Service - FastAPI Application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from eis_common.config import get_settings

from .routers import claims, ai_config

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting AI Claims Service...")
    yield
    logger.info("Shutting down AI Claims Service...")


app = FastAPI(
    title="EIS-D365 AI Claims Service",
    description="AI-powered claims intake, triage, and fraud detection",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(claims.router, prefix="/api/v1/claims", tags=["Claims"])
app.include_router(ai_config.router, prefix="/api/v1/claims/ai", tags=["AI Configuration"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ai-claims"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "EIS-D365 AI Claims Service",
        "version": "0.1.0",
        "docs": "/docs",
    }
