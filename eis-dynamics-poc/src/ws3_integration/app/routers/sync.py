"""Sync endpoints for D365 ↔ EIS synchronization."""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from eis_common.config import get_settings

from ..services.sync_service import SyncService

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

sync_service = SyncService()


class SyncRequest(BaseModel):
    entity_type: str  # policy, claim, customer
    entity_id: Optional[str] = None  # None = sync all
    direction: str = "eis_to_d365"  # eis_to_d365, d365_to_eis, bidirectional


class SyncStatus(BaseModel):
    sync_id: str
    entity_type: str
    status: str  # pending, in_progress, completed, failed
    started_at: datetime
    completed_at: Optional[datetime] = None
    records_processed: int = 0
    records_failed: int = 0
    error_message: Optional[str] = None


# In-memory sync status tracking
_sync_jobs: dict = {}


@router.post("/trigger", response_model=SyncStatus)
async def trigger_sync(request: SyncRequest, background_tasks: BackgroundTasks):
    """Trigger a sync operation."""
    import uuid

    sync_id = f"SYNC-{str(uuid.uuid4())[:8].upper()}"

    status = SyncStatus(
        sync_id=sync_id,
        entity_type=request.entity_type,
        status="pending",
        started_at=datetime.utcnow(),
    )
    _sync_jobs[sync_id] = status

    # Run sync in background
    background_tasks.add_task(
        _run_sync,
        sync_id,
        request.entity_type,
        request.entity_id,
        request.direction,
    )

    logger.info(f"Triggered sync {sync_id} for {request.entity_type}")
    return status


async def _run_sync(
    sync_id: str,
    entity_type: str,
    entity_id: Optional[str],
    direction: str,
):
    """Execute sync operation."""
    status = _sync_jobs[sync_id]
    status.status = "in_progress"

    try:
        if direction == "eis_to_d365":
            result = await sync_service.sync_eis_to_dataverse(entity_type, entity_id)
        else:
            result = await sync_service.sync_dataverse_to_eis(entity_type, entity_id)

        status.status = "completed"
        status.completed_at = datetime.utcnow()
        status.records_processed = result.get("processed", 0)
        status.records_failed = result.get("failed", 0)

        logger.info(f"Sync {sync_id} completed: {status.records_processed} processed")

    except Exception as e:
        status.status = "failed"
        status.completed_at = datetime.utcnow()
        status.error_message = str(e)
        logger.error(f"Sync {sync_id} failed: {e}")


@router.get("/status/{sync_id}", response_model=SyncStatus)
async def get_sync_status(sync_id: str):
    """Get status of a sync operation."""
    status = _sync_jobs.get(sync_id)
    if not status:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Sync job not found")

    return status


@router.get("/history")
async def get_sync_history(limit: int = 20):
    """Get recent sync history."""
    jobs = list(_sync_jobs.values())
    jobs.sort(key=lambda x: x.started_at, reverse=True)
    return jobs[:limit]


@router.post("/webhook/eis")
async def handle_eis_webhook(payload: dict, background_tasks: BackgroundTasks):
    """Handle incoming webhook from EIS system."""
    event_type = payload.get("event_type")
    entity_id = payload.get("entity_id")
    entity_type = payload.get("entity_type")

    logger.info(f"Received EIS webhook: {event_type} for {entity_type}/{entity_id}")

    # Queue sync for this entity
    background_tasks.add_task(
        sync_service.sync_eis_to_dataverse,
        entity_type,
        entity_id,
    )

    return {"status": "accepted", "message": f"Queued sync for {entity_id}"}
