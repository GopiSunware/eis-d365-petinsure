"""
Event-related Pydantic models for real-time streaming.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of pipeline events."""
    # Pipeline lifecycle
    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"

    # Agent lifecycle
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"

    # Step events
    STEP_STARTED = "step.started"
    STEP_COMPLETED = "step.completed"
    STEP_REASONING = "step.reasoning"

    # Tool events
    TOOL_CALLED = "tool.called"
    TOOL_RESULT = "tool.result"
    TOOL_ERROR = "tool.error"

    # Data events
    DATA_VALIDATED = "data.validated"
    DATA_ENRICHED = "data.enriched"
    DATA_ANALYZED = "data.analyzed"

    # Decision events
    DECISION_MADE = "decision.made"
    ALERT_CREATED = "alert.created"

    # System events
    HEARTBEAT = "system.heartbeat"
    ERROR = "system.error"


class EventSeverity(str, Enum):
    """Event severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PipelineEvent(BaseModel):
    """Base event model for all pipeline events."""
    event_id: str = Field(default_factory=lambda: f"EVT-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    event_type: EventType
    run_id: str
    claim_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: EventSeverity = EventSeverity.INFO

    # Event data
    data: dict[str, Any] = Field(default_factory=dict)
    message: str = ""

    # Context
    agent_name: Optional[str] = None
    step_name: Optional[str] = None
    tool_name: Optional[str] = None


class AgentStartedEvent(PipelineEvent):
    """Event when an agent starts processing."""
    event_type: EventType = EventType.AGENT_STARTED

    agent_name: str
    total_steps: int = 0


class AgentCompletedEvent(PipelineEvent):
    """Event when an agent completes processing."""
    event_type: EventType = EventType.AGENT_COMPLETED

    agent_name: str
    processing_time_ms: float
    output_summary: dict[str, Any] = Field(default_factory=dict)


class AgentFailedEvent(PipelineEvent):
    """Event when an agent fails."""
    event_type: EventType = EventType.AGENT_FAILED
    severity: EventSeverity = EventSeverity.ERROR

    agent_name: str
    error: str
    error_details: Optional[dict] = None


class StepStartedEvent(PipelineEvent):
    """Event when a step starts."""
    event_type: EventType = EventType.STEP_STARTED

    step_name: str
    step_index: int = 0
    total_steps: int = 0


class StepCompletedEvent(PipelineEvent):
    """Event when a step completes."""
    event_type: EventType = EventType.STEP_COMPLETED

    step_name: str
    step_index: int = 0
    result_summary: str = ""
    processing_time_ms: float = 0.0


class StepReasoningEvent(PipelineEvent):
    """Event with agent reasoning at a step."""
    event_type: EventType = EventType.STEP_REASONING

    step_name: str
    reasoning: str
    reasoning_type: str = "analysis"  # analysis, decision, observation


class ToolCalledEvent(PipelineEvent):
    """Event when a tool is called."""
    event_type: EventType = EventType.TOOL_CALLED

    tool_name: str
    tool_input: dict[str, Any] = Field(default_factory=dict)


class ToolResultEvent(PipelineEvent):
    """Event with tool result."""
    event_type: EventType = EventType.TOOL_RESULT

    tool_name: str
    tool_output: dict[str, Any] = Field(default_factory=dict)
    processing_time_ms: float = 0.0
    success: bool = True


class DecisionMadeEvent(PipelineEvent):
    """Event when a decision is made."""
    event_type: EventType = EventType.DECISION_MADE

    decision: str
    confidence: float = 0.0
    reasoning: str = ""
    decision_type: str = "validation"  # validation, enrichment, risk, final


class AlertCreatedEvent(PipelineEvent):
    """Event when an alert is created."""
    event_type: EventType = EventType.ALERT_CREATED
    severity: EventSeverity = EventSeverity.WARNING

    alert_type: str
    alert_message: str
    action_required: bool = False
    recommended_action: Optional[str] = None


class WebSocketMessage(BaseModel):
    """Message format for WebSocket communication."""
    type: str = "event"
    event: PipelineEvent
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EventSubscription(BaseModel):
    """Subscription request for events."""
    run_id: Optional[str] = None  # If None, subscribe to all
    event_types: list[EventType] = Field(default_factory=list)  # If empty, subscribe to all
    include_reasoning: bool = True
    include_tool_events: bool = True


class EventBatch(BaseModel):
    """Batch of events for bulk operations."""
    events: list[PipelineEvent]
    batch_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
