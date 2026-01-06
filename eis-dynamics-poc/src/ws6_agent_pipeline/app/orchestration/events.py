"""
Event streaming system for real-time pipeline updates.

Supports both Redis pub/sub and in-memory event distribution.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Optional
from uuid import uuid4

from ..models import (
    AgentCompletedEvent,
    AgentFailedEvent,
    AgentStartedEvent,
    AlertCreatedEvent,
    DecisionMadeEvent,
    EventSeverity,
    EventType,
    PipelineEvent,
    StepCompletedEvent,
    StepReasoningEvent,
    StepStartedEvent,
    ToolCalledEvent,
    ToolResultEvent,
)

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Publishes pipeline events to subscribers.

    Supports Redis pub/sub for distributed systems and
    in-memory async queues for local WebSocket connections.
    """

    def __init__(self, use_redis: bool = False, redis_url: Optional[str] = None):
        self._use_redis = use_redis
        self._redis_url = redis_url
        self._redis = None
        self._local_subscribers: dict[str, asyncio.Queue] = {}
        self._channel_name = "pipeline:events"
        self._running = False

    async def initialize(self):
        """Initialize the event publisher."""
        if self._use_redis and self._redis_url:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(self._redis_url)
                await self._redis.ping()
                logger.info("Event publisher connected to Redis")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis for events: {e}")
                self._use_redis = False

        self._running = True

    async def close(self):
        """Close the event publisher."""
        self._running = False
        if self._redis:
            await self._redis.close()

        # Close all local subscriber queues
        for queue in self._local_subscribers.values():
            await queue.put(None)  # Signal to stop

    def subscribe(self, subscriber_id: Optional[str] = None) -> tuple[str, asyncio.Queue]:
        """
        Subscribe to events and get a queue for receiving them.

        Returns: (subscriber_id, queue)
        """
        if not subscriber_id:
            subscriber_id = f"sub-{uuid4().hex[:8]}"

        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._local_subscribers[subscriber_id] = queue
        logger.info(f"Subscriber {subscriber_id} registered")
        return subscriber_id, queue

    def unsubscribe(self, subscriber_id: str):
        """Unsubscribe from events."""
        if subscriber_id in self._local_subscribers:
            del self._local_subscribers[subscriber_id]
            logger.info(f"Subscriber {subscriber_id} unregistered")

    async def publish(self, event: PipelineEvent):
        """Publish an event to all subscribers."""
        event_data = event.model_dump_json()

        # Publish to Redis
        if self._use_redis and self._redis:
            try:
                await self._redis.publish(self._channel_name, event_data)
            except Exception as e:
                logger.error(f"Failed to publish to Redis: {e}")

        # Publish to local subscribers
        for subscriber_id, queue in list(self._local_subscribers.items()):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"Queue full for subscriber {subscriber_id}")
            except Exception as e:
                logger.error(f"Error publishing to {subscriber_id}: {e}")

    async def publish_pipeline_started(
        self,
        run_id: str,
        claim_id: str,
        claim_data: dict[str, Any],
    ):
        """Publish pipeline started event."""
        event = PipelineEvent(
            event_type=EventType.PIPELINE_STARTED,
            run_id=run_id,
            claim_id=claim_id,
            message=f"Pipeline started for claim {claim_id}",
            data={"claim_data": claim_data},
        )
        await self.publish(event)

    async def publish_pipeline_completed(
        self,
        run_id: str,
        claim_id: str,
        processing_time_ms: float,
        final_decision: str,
        summary: dict[str, Any],
    ):
        """Publish pipeline completed event."""
        event = PipelineEvent(
            event_type=EventType.PIPELINE_COMPLETED,
            run_id=run_id,
            claim_id=claim_id,
            message=f"Pipeline completed: {final_decision}",
            data={
                "processing_time_ms": processing_time_ms,
                "final_decision": final_decision,
                "summary": summary,
            },
        )
        await self.publish(event)

    async def publish_pipeline_failed(
        self,
        run_id: str,
        claim_id: str,
        error: str,
        error_details: Optional[dict] = None,
    ):
        """Publish pipeline failed event."""
        event = PipelineEvent(
            event_type=EventType.PIPELINE_FAILED,
            run_id=run_id,
            claim_id=claim_id,
            severity=EventSeverity.ERROR,
            message=f"Pipeline failed: {error}",
            data={
                "error": error,
                "error_details": error_details,
            },
        )
        await self.publish(event)

    async def publish_agent_started(
        self,
        run_id: str,
        claim_id: str,
        agent_name: str,
        total_steps: int = 0,
    ):
        """Publish agent started event."""
        event = AgentStartedEvent(
            run_id=run_id,
            claim_id=claim_id,
            agent_name=agent_name,
            total_steps=total_steps,
            message=f"{agent_name.title()} Agent started",
        )
        await self.publish(event)

    async def publish_agent_completed(
        self,
        run_id: str,
        claim_id: str,
        agent_name: str,
        processing_time_ms: float,
        output_summary: dict[str, Any],
    ):
        """Publish agent completed event."""
        event = AgentCompletedEvent(
            run_id=run_id,
            claim_id=claim_id,
            agent_name=agent_name,
            processing_time_ms=processing_time_ms,
            output_summary=output_summary,
            message=f"{agent_name.title()} Agent completed in {processing_time_ms:.0f}ms",
        )
        await self.publish(event)

    async def publish_agent_failed(
        self,
        run_id: str,
        claim_id: str,
        agent_name: str,
        error: str,
        error_details: Optional[dict] = None,
    ):
        """Publish agent failed event."""
        event = AgentFailedEvent(
            run_id=run_id,
            claim_id=claim_id,
            agent_name=agent_name,
            error=error,
            error_details=error_details,
            message=f"{agent_name.title()} Agent failed: {error}",
        )
        await self.publish(event)

    async def publish_step_started(
        self,
        run_id: str,
        claim_id: str,
        agent_name: str,
        step_name: str,
        step_index: int = 0,
        total_steps: int = 0,
    ):
        """Publish step started event."""
        event = StepStartedEvent(
            run_id=run_id,
            claim_id=claim_id,
            agent_name=agent_name,
            step_name=step_name,
            step_index=step_index,
            total_steps=total_steps,
            message=f"Starting: {step_name}",
        )
        await self.publish(event)

    async def publish_step_completed(
        self,
        run_id: str,
        claim_id: str,
        agent_name: str,
        step_name: str,
        step_index: int = 0,
        result_summary: str = "",
        processing_time_ms: float = 0.0,
    ):
        """Publish step completed event."""
        event = StepCompletedEvent(
            run_id=run_id,
            claim_id=claim_id,
            agent_name=agent_name,
            step_name=step_name,
            step_index=step_index,
            result_summary=result_summary,
            processing_time_ms=processing_time_ms,
            message=f"Completed: {step_name}",
        )
        await self.publish(event)

    async def publish_reasoning(
        self,
        run_id: str,
        claim_id: str,
        agent_name: str,
        step_name: str,
        reasoning: str,
        reasoning_type: str = "analysis",
    ):
        """Publish agent reasoning event."""
        event = StepReasoningEvent(
            run_id=run_id,
            claim_id=claim_id,
            agent_name=agent_name,
            step_name=step_name,
            reasoning=reasoning,
            reasoning_type=reasoning_type,
            message=reasoning[:100] + "..." if len(reasoning) > 100 else reasoning,
        )
        await self.publish(event)

    async def publish_tool_called(
        self,
        run_id: str,
        claim_id: str,
        agent_name: str,
        tool_name: str,
        tool_input: dict[str, Any],
    ):
        """Publish tool called event."""
        event = ToolCalledEvent(
            run_id=run_id,
            claim_id=claim_id,
            agent_name=agent_name,
            tool_name=tool_name,
            tool_input=tool_input,
            message=f"Calling tool: {tool_name}",
        )
        await self.publish(event)

    async def publish_tool_result(
        self,
        run_id: str,
        claim_id: str,
        agent_name: str,
        tool_name: str,
        tool_output: dict[str, Any],
        processing_time_ms: float = 0.0,
        success: bool = True,
    ):
        """Publish tool result event."""
        event = ToolResultEvent(
            run_id=run_id,
            claim_id=claim_id,
            agent_name=agent_name,
            tool_name=tool_name,
            tool_output=tool_output,
            processing_time_ms=processing_time_ms,
            success=success,
            severity=EventSeverity.INFO if success else EventSeverity.WARNING,
            message=f"Tool {tool_name} {'completed' if success else 'failed'}",
        )
        await self.publish(event)

    async def publish_decision(
        self,
        run_id: str,
        claim_id: str,
        agent_name: str,
        decision: str,
        confidence: float,
        reasoning: str,
        decision_type: str = "validation",
    ):
        """Publish decision made event."""
        event = DecisionMadeEvent(
            run_id=run_id,
            claim_id=claim_id,
            agent_name=agent_name,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            decision_type=decision_type,
            message=f"Decision: {decision} (confidence: {confidence:.0%})",
        )
        await self.publish(event)

    async def publish_alert(
        self,
        run_id: str,
        claim_id: str,
        agent_name: str,
        alert_type: str,
        alert_message: str,
        severity: EventSeverity = EventSeverity.WARNING,
        action_required: bool = False,
        recommended_action: Optional[str] = None,
    ):
        """Publish alert event."""
        event = AlertCreatedEvent(
            run_id=run_id,
            claim_id=claim_id,
            agent_name=agent_name,
            alert_type=alert_type,
            alert_message=alert_message,
            severity=severity,
            action_required=action_required,
            recommended_action=recommended_action,
            message=alert_message,
        )
        await self.publish(event)


class EventContext:
    """
    Context manager for publishing events within an agent execution.

    Provides convenience methods for common event patterns.
    """

    def __init__(
        self,
        publisher: EventPublisher,
        run_id: str,
        claim_id: str,
        agent_name: str,
    ):
        self.publisher = publisher
        self.run_id = run_id
        self.claim_id = claim_id
        self.agent_name = agent_name
        self._step_index = 0
        self._total_steps = 0

    def set_total_steps(self, total: int):
        """Set total number of steps for progress tracking."""
        self._total_steps = total

    async def start_step(self, step_name: str):
        """Start a new step."""
        await self.publisher.publish_step_started(
            run_id=self.run_id,
            claim_id=self.claim_id,
            agent_name=self.agent_name,
            step_name=step_name,
            step_index=self._step_index,
            total_steps=self._total_steps,
        )

    async def complete_step(
        self,
        step_name: str,
        result_summary: str = "",
        processing_time_ms: float = 0.0,
    ):
        """Complete a step."""
        await self.publisher.publish_step_completed(
            run_id=self.run_id,
            claim_id=self.claim_id,
            agent_name=self.agent_name,
            step_name=step_name,
            step_index=self._step_index,
            result_summary=result_summary,
            processing_time_ms=processing_time_ms,
        )
        self._step_index += 1

    async def reason(self, reasoning: str, reasoning_type: str = "analysis"):
        """Publish reasoning."""
        await self.publisher.publish_reasoning(
            run_id=self.run_id,
            claim_id=self.claim_id,
            agent_name=self.agent_name,
            step_name=f"step_{self._step_index}",
            reasoning=reasoning,
            reasoning_type=reasoning_type,
        )

    async def call_tool(self, tool_name: str, tool_input: dict[str, Any]):
        """Record tool call."""
        await self.publisher.publish_tool_called(
            run_id=self.run_id,
            claim_id=self.claim_id,
            agent_name=self.agent_name,
            tool_name=tool_name,
            tool_input=tool_input,
        )

    async def tool_result(
        self,
        tool_name: str,
        tool_output: dict[str, Any],
        processing_time_ms: float = 0.0,
        success: bool = True,
    ):
        """Record tool result."""
        await self.publisher.publish_tool_result(
            run_id=self.run_id,
            claim_id=self.claim_id,
            agent_name=self.agent_name,
            tool_name=tool_name,
            tool_output=tool_output,
            processing_time_ms=processing_time_ms,
            success=success,
        )

    async def decide(
        self,
        decision: str,
        confidence: float,
        reasoning: str,
        decision_type: str = "validation",
    ):
        """Publish decision."""
        await self.publisher.publish_decision(
            run_id=self.run_id,
            claim_id=self.claim_id,
            agent_name=self.agent_name,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            decision_type=decision_type,
        )

    async def alert(
        self,
        alert_type: str,
        alert_message: str,
        severity: EventSeverity = EventSeverity.WARNING,
        action_required: bool = False,
        recommended_action: Optional[str] = None,
    ):
        """Create alert."""
        await self.publisher.publish_alert(
            run_id=self.run_id,
            claim_id=self.claim_id,
            agent_name=self.agent_name,
            alert_type=alert_type,
            alert_message=alert_message,
            severity=severity,
            action_required=action_required,
            recommended_action=recommended_action,
        )


# Global event publisher instance
event_publisher = EventPublisher()
