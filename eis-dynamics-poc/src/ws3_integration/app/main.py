"""WS3: Integration Layer - FastAPI Application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from eis_common.config import get_settings

from .routers import eis_mock, sync

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Integration Service...")
    yield
    logger.info("Shutting down Integration Service...")


app = FastAPI(
    title="EIS-D365 Pet Insurance Integration Service",
    description="Mock EIS Pet Insurance APIs and D365 Dataverse sync layer",
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

app.include_router(eis_mock.router, prefix="/api/v1/eis", tags=["Mock EIS"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["Sync"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "integration"}


@app.get("/")
async def root():
    return {
        "service": "EIS-D365 Integration Service",
        "version": "0.1.0",
        "docs": "/docs",
    }
