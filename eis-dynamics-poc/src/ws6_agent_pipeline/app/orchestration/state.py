"""
Pipeline state management for LangGraph orchestration.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from ..models import (
    AgentState,
    AgentStatus,
    PipelineStage,
    PipelineState,
    PipelineStatus,
)

logger = logging.getLogger(__name__)


class PipelineStateManager:
    """
    Manages pipeline state across agent executions.

    Uses in-memory storage with optional Redis persistence.
    """

    def __init__(self, use_redis: bool = False, redis_url: Optional[str] = None):
        self._states: dict[str, PipelineState] = {}
        self._lock = asyncio.Lock()
        self._use_redis = use_redis
        self._redis_url = redis_url
        self._redis = None

    async def initialize(self):
        """Initialize state manager, optionally connecting to Redis."""
        if self._use_redis and self._redis_url:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(self._redis_url)
                await self._redis.ping()
                logger.info("Connected to Redis for state persistence")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis, using in-memory only: {e}")
                self._use_redis = False

    async def close(self):
        """Close connections."""
        if self._redis:
            await self._redis.close()

    def generate_run_id(self) -> str:
        """Generate a unique run ID."""
        return f"RUN-{uuid4().hex[:8].upper()}"

    async def create_pipeline_state(
        self,
        run_id: str,
        claim_id: str,
        claim_data: dict[str, Any],
        complexity: str = "medium",
    ) -> PipelineState:
        """Create a new pipeline state."""
        state = PipelineState(
            run_id=run_id,
            claim_id=claim_id,
            status=PipelineStatus.STARTED,
            current_stage=PipelineStage.TRIGGER,
            started_at=datetime.utcnow(),
            claim_data=claim_data,
            complexity=complexity,
        )

        async with self._lock:
            self._states[run_id] = state
            if self._use_redis and self._redis:
                await self._redis.set(
                    f"pipeline:state:{run_id}",
                    state.model_dump_json(),
                    ex=86400,  # 24 hour expiry
                )

        logger.info(f"Created pipeline state for run {run_id}")
        return state

    async def get_pipeline_state(self, run_id: str) -> Optional[PipelineState]:
        """Get pipeline state by run ID."""
        async with self._lock:
            if run_id in self._states:
                return self._states[run_id]

            # Try Redis if not in memory
            if self._use_redis and self._redis:
                data = await self._redis.get(f"pipeline:state:{run_id}")
                if data:
                    state = PipelineState.model_validate_json(data)
                    self._states[run_id] = state
                    return state

        return None

    async def update_pipeline_state(
        self,
        run_id: str,
        **updates: Any,
    ) -> Optional[PipelineState]:
        """Update pipeline state with given fields."""
        async with self._lock:
            state = self._states.get(run_id)
            if not state:
                return None

            # Apply updates
            for key, value in updates.items():
                if hasattr(state, key):
                    setattr(state, key, value)

            # Persist to Redis
            if self._use_redis and self._redis:
                await self._redis.set(
                    f"pipeline:state:{run_id}",
                    state.model_dump_json(),
                    ex=86400,
                )

            return state

    async def update_stage(
        self,
        run_id: str,
        stage: PipelineStage,
    ) -> Optional[PipelineState]:
        """Update current pipeline stage."""
        return await self.update_pipeline_state(
            run_id,
            current_stage=stage,
            status=PipelineStatus.RUNNING,
        )

    async def start_agent(
        self,
        run_id: str,
        agent_name: str,
        total_steps: int = 0,
    ) -> Optional[AgentState]:
        """Mark an agent as started."""
        agent_state = AgentState(
            agent_name=agent_name,
            status=AgentStatus.RUNNING,
            started_at=datetime.utcnow(),
            total_steps=total_steps,
        )

        state_field = f"{agent_name}_state"
        await self.update_pipeline_state(run_id, **{state_field: agent_state})

        logger.info(f"Agent {agent_name} started for run {run_id}")
        return agent_state

    async def complete_agent(
        self,
        run_id: str,
        agent_name: str,
        output: dict[str, Any],
        reasoning_log: Optional[list[str]] = None,
    ) -> Optional[AgentState]:
        """Mark an agent as completed."""
        state = await self.get_pipeline_state(run_id)
        if not state:
            return None

        state_field = f"{agent_name}_state"
        agent_state: Optional[AgentState] = getattr(state, state_field, None)

        if agent_state:
            agent_state.status = AgentStatus.COMPLETED
            agent_state.completed_at = datetime.utcnow()
            agent_state.output = output
            if reasoning_log:
                agent_state.reasoning_log = reasoning_log

            if agent_state.started_at:
                agent_state.processing_time_ms = (
                    agent_state.completed_at - agent_state.started_at
                ).total_seconds() * 1000

            await self.update_pipeline_state(run_id, **{state_field: agent_state})
            logger.info(f"Agent {agent_name} completed for run {run_id}")

        return agent_state

    async def fail_agent(
        self,
        run_id: str,
        agent_name: str,
        error: str,
        error_details: Optional[dict] = None,
    ) -> Optional[AgentState]:
        """Mark an agent as failed."""
        state = await self.get_pipeline_state(run_id)
        if not state:
            return None

        state_field = f"{agent_name}_state"
        agent_state: Optional[AgentState] = getattr(state, state_field, None)

        if agent_state:
            agent_state.status = AgentStatus.FAILED
            agent_state.completed_at = datetime.utcnow()
            agent_state.error = error
            agent_state.error_details = error_details

            await self.update_pipeline_state(
                run_id,
                **{state_field: agent_state},
                has_errors=True,
            )
            logger.error(f"Agent {agent_name} failed for run {run_id}: {error}")

        return agent_state

    async def add_agent_step(
        self,
        run_id: str,
        agent_name: str,
        step_name: str,
        is_current: bool = True,
    ):
        """Add a step to agent's progress."""
        state = await self.get_pipeline_state(run_id)
        if not state:
            return

        state_field = f"{agent_name}_state"
        agent_state: Optional[AgentState] = getattr(state, state_field, None)

        if agent_state:
            if is_current:
                agent_state.current_step = step_name
            agent_state.steps_completed.append(step_name)
            await self.update_pipeline_state(run_id, **{state_field: agent_state})

    async def add_tool_call(
        self,
        run_id: str,
        agent_name: str,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: Optional[dict[str, Any]] = None,
    ):
        """Record a tool call."""
        state = await self.get_pipeline_state(run_id)
        if not state:
            return

        state_field = f"{agent_name}_state"
        agent_state: Optional[AgentState] = getattr(state, state_field, None)

        if agent_state:
            agent_state.tool_calls.append({
                "tool_name": tool_name,
                "input": tool_input,
                "output": tool_output,
                "timestamp": datetime.utcnow().isoformat(),
            })
            await self.update_pipeline_state(run_id, **{state_field: agent_state})

    async def add_reasoning(
        self,
        run_id: str,
        agent_name: str,
        reasoning: str,
    ):
        """Add reasoning to agent's log."""
        state = await self.get_pipeline_state(run_id)
        if not state:
            return

        state_field = f"{agent_name}_state"
        agent_state: Optional[AgentState] = getattr(state, state_field, None)

        if agent_state:
            agent_state.reasoning_log.append(reasoning)
            await self.update_pipeline_state(run_id, **{state_field: agent_state})

    async def set_layer_output(
        self,
        run_id: str,
        layer: str,  # bronze, silver, gold
        output: dict[str, Any],
    ):
        """Set output for a specific layer."""
        output_field = f"{layer}_output"
        await self.update_pipeline_state(run_id, **{output_field: output})

    async def complete_pipeline(
        self,
        run_id: str,
        final_decision: str,
        fraud_score: Optional[float] = None,
        risk_level: Optional[str] = None,
        insights: Optional[list[str]] = None,
    ) -> Optional[PipelineState]:
        """Mark pipeline as completed."""
        state = await self.get_pipeline_state(run_id)
        if not state:
            return None

        completed_at = datetime.utcnow()
        total_time_ms = 0.0
        if state.started_at:
            total_time_ms = (completed_at - state.started_at).total_seconds() * 1000

        return await self.update_pipeline_state(
            run_id,
            status=PipelineStatus.COMPLETED,
            current_stage=PipelineStage.COMPLETED,
            completed_at=completed_at,
            total_processing_time_ms=total_time_ms,
            final_decision=final_decision,
            fraud_score=fraud_score,
            risk_level=risk_level,
            insights=insights or [],
        )

    async def fail_pipeline(
        self,
        run_id: str,
        error: str,
        error_details: Optional[dict] = None,
    ) -> Optional[PipelineState]:
        """Mark pipeline as failed."""
        state = await self.get_pipeline_state(run_id)
        if not state:
            return None

        errors = state.errors.copy()
        errors.append({
            "error": error,
            "details": error_details,
            "timestamp": datetime.utcnow().isoformat(),
        })

        return await self.update_pipeline_state(
            run_id,
            status=PipelineStatus.FAILED,
            current_stage=PipelineStage.ERROR,
            completed_at=datetime.utcnow(),
            errors=errors,
            has_errors=True,
        )

    async def initialize_pending_run(
        self,
        run_id: str,
        claim_id: str,
        claim_data: dict[str, Any],
    ) -> PipelineState:
        """
        Initialize a pipeline run in 'pending' status for manual processing.

        The run will wait for user action to start Bronze processing.
        """
        state = PipelineState(
            run_id=run_id,
            claim_id=claim_id,
            status=PipelineStatus.PENDING,
            current_stage=PipelineStage.TRIGGER,
            started_at=datetime.utcnow(),
            claim_data=claim_data,
            complexity="pending",  # Will be determined by router
        )

        async with self._lock:
            self._states[run_id] = state
            if self._use_redis and self._redis:
                await self._redis.set(
                    f"pipeline:state:{run_id}",
                    state.model_dump_json(),
                    ex=86400,
                )

        logger.info(f"Created pending pipeline state for run {run_id}")
        return state

    async def get_pending_runs(self) -> list[PipelineState]:
        """Get all pipeline runs waiting for manual processing."""
        async with self._lock:
            return [
                state for state in self._states.values()
                if state.status == PipelineStatus.PENDING
            ]

    async def get_all_active_runs(self) -> list[PipelineState]:
        """Get all currently active pipeline runs."""
        async with self._lock:
            return [
                state for state in self._states.values()
                if state.status in (PipelineStatus.STARTED, PipelineStatus.RUNNING)
            ]

    async def get_recent_runs(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PipelineState]:
        """Get recent pipeline runs."""
        async with self._lock:
            sorted_states = sorted(
                self._states.values(),
                key=lambda s: s.started_at or datetime.min,
                reverse=True,
            )
            return sorted_states[offset:offset + limit]

    async def cleanup_old_runs(self, max_age_hours: int = 24):
        """Remove old completed runs from memory."""
        cutoff = datetime.utcnow()
        async with self._lock:
            to_remove = []
            for run_id, state in self._states.items():
                if state.completed_at:
                    age_hours = (cutoff - state.completed_at).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        to_remove.append(run_id)

            for run_id in to_remove:
                del self._states[run_id]

            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} old pipeline runs")

    async def clear_all_runs(self) -> int:
        """Clear all pipeline runs (for demo reset)."""
        async with self._lock:
            count = len(self._states)
            self._states.clear()

            # Also clear Redis if enabled
            if self._use_redis and self._redis:
                try:
                    keys = await self._redis.keys("pipeline:state:*")
                    if keys:
                        await self._redis.delete(*keys)
                except Exception as e:
                    logger.warning(f"Failed to clear Redis keys: {e}")

            logger.info(f"Cleared all {count} pipeline runs")
            return count


# Global state manager instance
state_manager = PipelineStateManager()
