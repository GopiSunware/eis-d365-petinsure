"""
Pipeline-related Pydantic models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    """Pipeline processing stages."""
    TRIGGER = "trigger"
    ROUTER = "router"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    COMPLETED = "completed"
    ERROR = "error"


class PipelineStatus(str, Enum):
    """Overall pipeline status."""
    PENDING = "pending"
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(str, Enum):
    """Individual agent status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TriggerRequest(BaseModel):
    """Request to trigger pipeline processing."""
    event_type: str = "claim.submitted"
    source: str = "petinsure360"
    claim_id: str
    claim_data: dict[str, Any]
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TriggerResponse(BaseModel):
    """Response after triggering pipeline."""
    run_id: str
    claim_id: str
    status: PipelineStatus
    current_stage: PipelineStage
    started_at: datetime
    message: str = "Pipeline started successfully"


class AgentState(BaseModel):
    """State of an individual agent."""
    agent_name: str
    status: AgentStatus = AgentStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_ms: float = 0.0

    # Current step
    current_step: Optional[str] = None
    steps_completed: list[str] = Field(default_factory=list)
    total_steps: int = 0

    # Tool calls
    tool_calls: list[dict] = Field(default_factory=list)

    # Reasoning
    reasoning_log: list[str] = Field(default_factory=list)

    # Output
    output: dict[str, Any] = Field(default_factory=dict)

    # Errors
    error: Optional[str] = None
    error_details: Optional[dict] = None


class PipelineState(BaseModel):
    """Complete pipeline state for a run."""
    run_id: str
    claim_id: str
    status: PipelineStatus = PipelineStatus.PENDING
    current_stage: PipelineStage = PipelineStage.TRIGGER

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_processing_time_ms: float = 0.0

    # Claim data
    claim_data: dict[str, Any] = Field(default_factory=dict)
    complexity: str = "medium"

    # Agent states
    router_state: Optional[AgentState] = None
    bronze_state: Optional[AgentState] = None
    silver_state: Optional[AgentState] = None
    gold_state: Optional[AgentState] = None

    # Results at each layer
    bronze_output: Optional[dict] = None
    silver_output: Optional[dict] = None
    gold_output: Optional[dict] = None

    # Final results
    final_decision: Optional[str] = None
    fraud_score: Optional[float] = None
    risk_level: Optional[str] = None
    insights: list[str] = Field(default_factory=list)

    # Errors
    errors: list[dict] = Field(default_factory=list)
    has_errors: bool = False

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)


class PipelineRunSummary(BaseModel):
    """Summary of a pipeline run for list views."""
    run_id: str
    claim_id: str
    status: PipelineStatus
    current_stage: PipelineStage
    complexity: str

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_ms: float = 0.0

    # Quick results
    decision: Optional[str] = None
    fraud_score: Optional[float] = None
    risk_level: Optional[str] = None

    # Progress
    stages_completed: int = 0
    total_stages: int = 4  # router, bronze, silver, gold


class PipelineHistoryRequest(BaseModel):
    """Request for pipeline history."""
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
    status: Optional[PipelineStatus] = None
    claim_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class PipelineHistoryResponse(BaseModel):
    """Response with pipeline history."""
    runs: list[PipelineRunSummary]
    total: int
    limit: int
    offset: int


class PipelineMetrics(BaseModel):
    """Aggregated pipeline metrics."""
    total_runs: int = 0
    completed_runs: int = 0
    failed_runs: int = 0
    running_runs: int = 0

    # Timing averages
    avg_processing_time_ms: float = 0.0
    avg_bronze_time_ms: float = 0.0
    avg_silver_time_ms: float = 0.0
    avg_gold_time_ms: float = 0.0

    # Decision distribution
    auto_approved: int = 0
    manual_review: int = 0
    denied: int = 0

    # Risk distribution
    low_risk: int = 0
    medium_risk: int = 0
    high_risk: int = 0
    critical_risk: int = 0

    # Period
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
