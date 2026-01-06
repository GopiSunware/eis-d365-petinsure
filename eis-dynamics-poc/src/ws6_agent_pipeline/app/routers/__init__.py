"""
API routers for the Agent Pipeline service.
"""

from .pipeline import router as pipeline_router
from .status import router as status_router
from .websocket import router as websocket_router
from .scenarios import router as scenarios_router
from .comparison import router as comparison_router

__all__ = [
    "pipeline_router",
    "status_router",
    "websocket_router",
    "scenarios_router",
    "comparison_router",
]
