"""WS5: Rating Engine - FastAPI Application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from eis_common.config import get_settings

from .routers import rating

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Rating Engine...")
    yield
    logger.info("Shutting down Rating Engine...")


app = FastAPI(
    title="EIS-D365 Pet Insurance Rating Engine",
    description="Pet insurance premium calculation service with breed-specific rating factors",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rating.router, prefix="/api/v1/rating", tags=["Rating"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rating-engine"}


@app.get("/")
async def root():
    return {
        "service": "EIS-D365 Pet Insurance Rating Engine",
        "version": "0.1.0",
        "docs": "/docs",
    }
