"""
Main pipeline orchestration using LangGraph.

Coordinates the Router, Bronze, Silver, and Gold agents
for end-to-end claim processing.
"""

import logging
from datetime import datetime
from typing import Any, Literal, Optional

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from ..agents import bronze_agent, gold_agent, router_agent, silver_agent
from ..models import PipelineStage, PipelineStatus
from ..services.s3_service import get_s3_service
from .events import event_publisher
from .state import state_manager

logger = logging.getLogger(__name__)


class MedallionPipelineState(BaseModel):
    """State for the complete medallion pipeline."""
    # Identifiers
    run_id: str = ""
    claim_id: str = ""

    # Input data
    claim_data: dict[str, Any] = Field(default_factory=dict)

    # Current stage
    current_stage: str = "trigger"

    # Router results
    complexity: str = "medium"
    processing_path: str = "standard"

    # Agent outputs
    router_output: Optional[dict] = None
    bronze_output: Optional[dict] = None
    silver_output: Optional[dict] = None
    gold_output: Optional[dict] = None

    # Final results
    final_decision: str = "pending"
    fraud_score: float = 0.0
    risk_level: str = "unknown"
    insights: list[str] = Field(default_factory=list)

    # Timing
    started_at: Optional[datetime] = None
    total_processing_time_ms: float = 0.0

    # Status
    status: str = "running"
    error: Optional[str] = None


class MedallionPipeline:
    """
    Main pipeline orchestrator for the medallion architecture.

    Coordinates:
    1. Router Agent - Determines claim complexity
    2. Bronze Agent - Validates and cleans data
    3. Silver Agent - Enriches and transforms data
    4. Gold Agent - Generates analytics and insights
    """

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the complete pipeline graph."""
        graph = StateGraph(MedallionPipelineState)

        # Add nodes for each stage
        graph.add_node("router", self._router_node)
        graph.add_node("bronze", self._bronze_node)
        graph.add_node("silver", self._silver_node)
        graph.add_node("gold", self._gold_node)

        # Set entry point
        graph.set_entry_point("router")

        # Add edges
        graph.add_conditional_edges(
            "router",
            self._after_router,
            {
                "continue": "bronze",
                "end": END,
            }
        )

        graph.add_conditional_edges(
            "bronze",
            self._after_bronze,
            {
                "continue": "silver",
                "end": END,
            }
        )

        graph.add_conditional_edges(
            "silver",
            self._after_silver,
            {
                "continue": "gold",
                "end": END,
            }
        )

        graph.add_edge("gold", END)

        return graph.compile()

    def _after_router(self, state: MedallionPipelineState) -> Literal["continue", "end"]:
        """Determine next step after router."""
        if state.error:
            return "end"
        return "continue"

    def _after_bronze(self, state: MedallionPipelineState) -> Literal["continue", "end"]:
        """Determine next step after bronze."""
        if state.error:
            return "end"

        # Check if bronze rejected the claim
        bronze_decision = state.bronze_output.get("decision", "accept") if state.bronze_output else "accept"
        if bronze_decision == "reject":
            logger.info(f"Bronze rejected claim {state.claim_id}, ending pipeline")
            return "end"

        return "continue"

    def _after_silver(self, state: MedallionPipelineState) -> Literal["continue", "end"]:
        """Determine next step after silver."""
        if state.error:
            return "end"
        return "continue"

    async def _router_node(self, state: MedallionPipelineState) -> dict:
        """Execute router agent."""
        try:
            # Update stage
            await state_manager.update_stage(state.run_id, PipelineStage.ROUTER)

            # Run router
            result = await router_agent.route(
                run_id=state.run_id,
                claim_id=state.claim_id,
                claim_data=state.claim_data,
            )

            return {
                "current_stage": "router",
                "router_output": result,
                "complexity": result.get("complexity", "medium"),
                "processing_path": result.get("processing_path", "standard"),
            }

        except Exception as e:
            logger.error(f"Router node error: {e}")
            return {
                "error": str(e),
                "status": "failed",
            }

    async def _bronze_node(self, state: MedallionPipelineState) -> dict:
        """Execute bronze agent."""
        try:
            # Update stage
            await state_manager.update_stage(state.run_id, PipelineStage.BRONZE)

            # Run bronze agent
            result = await bronze_agent.process(
                run_id=state.run_id,
                claim_id=state.claim_id,
                claim_data=state.claim_data,
            )

            # Store bronze output in state manager
            await state_manager.set_layer_output(state.run_id, "bronze", result)

            # Write bronze output to S3 Data Lake
            s3_service = get_s3_service()
            s3_path = s3_service.write_bronze_output(state.claim_id, state.run_id, result)
            if s3_path:
                logger.info(f"Bronze output stored at: {s3_path}")

            return {
                "current_stage": "bronze",
                "bronze_output": result,
            }

        except Exception as e:
            logger.error(f"Bronze node error: {e}")
            return {
                "error": str(e),
                "status": "failed",
            }

    async def _silver_node(self, state: MedallionPipelineState) -> dict:
        """Execute silver agent."""
        try:
            # Update stage
            await state_manager.update_stage(state.run_id, PipelineStage.SILVER)

            # Run silver agent
            result = await silver_agent.process(
                run_id=state.run_id,
                claim_id=state.claim_id,
                bronze_data=state.bronze_output or {},
            )

            # Store silver output in state manager
            await state_manager.set_layer_output(state.run_id, "silver", result)

            # Write silver output to S3 Data Lake
            s3_service = get_s3_service()
            s3_path = s3_service.write_silver_output(state.claim_id, state.run_id, result)
            if s3_path:
                logger.info(f"Silver output stored at: {s3_path}")

            return {
                "current_stage": "silver",
                "silver_output": result,
            }

        except Exception as e:
            logger.error(f"Silver node error: {e}")
            return {
                "error": str(e),
                "status": "failed",
            }

    async def _gold_node(self, state: MedallionPipelineState) -> dict:
        """Execute gold agent."""
        try:
            # Update stage
            await state_manager.update_stage(state.run_id, PipelineStage.GOLD)

            # Calculate processing time so far (with defensive type checking)
            processing_time_so_far = 0.0
            if state.bronze_output and isinstance(state.bronze_output, dict):
                processing_time_so_far += state.bronze_output.get("processing_time_ms", 0)
            if state.silver_output and isinstance(state.silver_output, dict):
                processing_time_so_far += state.silver_output.get("processing_time_ms", 0)

            # Ensure silver_data is a dict (defensive)
            silver_data = state.silver_output if isinstance(state.silver_output, dict) else {}

            # Run gold agent
            result = await gold_agent.process(
                run_id=state.run_id,
                claim_id=state.claim_id,
                silver_data=silver_data,
                total_processing_time_ms=processing_time_so_far,
            )

            # Store gold output in state manager
            await state_manager.set_layer_output(state.run_id, "gold", result)

            # Write gold output to S3 Data Lake
            s3_service = get_s3_service()
            s3_path = s3_service.write_gold_output(state.claim_id, state.run_id, result)
            if s3_path:
                logger.info(f"Gold output stored at: {s3_path}")

            return {
                "current_stage": "gold",
                "gold_output": result,
                "final_decision": result.get("final_decision", "unknown"),
                "fraud_score": result.get("fraud_score", 0.0),
                "risk_level": result.get("risk_level", "unknown"),
                "insights": result.get("insights", []),
                "status": "completed",
            }

        except Exception as e:
            logger.error(f"Gold node error: {e}")
            return {
                "error": str(e),
                "status": "failed",
            }

    async def process_claim(
        self,
        run_id: str,
        claim_id: str,
        claim_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Process a claim through the complete medallion pipeline.

        Args:
            run_id: Unique run identifier
            claim_id: Claim identifier
            claim_data: Raw claim data to process

        Returns:
            Complete pipeline results
        """
        start_time = datetime.utcnow()

        try:
            # Create pipeline state
            await state_manager.create_pipeline_state(
                run_id=run_id,
                claim_id=claim_id,
                claim_data=claim_data,
            )

            # Publish pipeline started
            await event_publisher.publish_pipeline_started(
                run_id=run_id,
                claim_id=claim_id,
                claim_data=claim_data,
            )

            # Initialize graph state
            initial_state = MedallionPipelineState(
                run_id=run_id,
                claim_id=claim_id,
                claim_data=claim_data,
                started_at=start_time,
            )

            # Run the pipeline
            final_state = await self.graph.ainvoke(initial_state)

            # Calculate total processing time
            end_time = datetime.utcnow()
            total_time_ms = (end_time - start_time).total_seconds() * 1000

            # Extract final results
            result = {
                "success": final_state.get("error") is None,
                "run_id": run_id,
                "claim_id": claim_id,
                "status": final_state.get("status", "completed"),
                "complexity": final_state.get("complexity", "medium"),
                "processing_path": final_state.get("processing_path", "standard"),
                "final_decision": final_state.get("final_decision", "unknown"),
                "fraud_score": final_state.get("fraud_score", 0.0),
                "risk_level": final_state.get("risk_level", "unknown"),
                "insights": final_state.get("insights", []),
                "total_processing_time_ms": total_time_ms,
                "bronze_output": final_state.get("bronze_output"),
                "silver_output": final_state.get("silver_output"),
                "gold_output": final_state.get("gold_output"),
                "error": final_state.get("error"),
            }

            # Complete or fail pipeline in state manager
            if result["success"]:
                await state_manager.complete_pipeline(
                    run_id=run_id,
                    final_decision=result["final_decision"],
                    fraud_score=result["fraud_score"],
                    risk_level=result["risk_level"],
                    insights=result["insights"],
                )

                # Publish pipeline completed
                await event_publisher.publish_pipeline_completed(
                    run_id=run_id,
                    claim_id=claim_id,
                    processing_time_ms=total_time_ms,
                    final_decision=result["final_decision"],
                    summary={
                        "fraud_score": result["fraud_score"],
                        "risk_level": result["risk_level"],
                        "complexity": result["complexity"],
                    },
                )
            else:
                await state_manager.fail_pipeline(
                    run_id=run_id,
                    error=result.get("error", "Unknown error"),
                )

                # Publish pipeline failed
                await event_publisher.publish_pipeline_failed(
                    run_id=run_id,
                    claim_id=claim_id,
                    error=result.get("error", "Unknown error"),
                )

            logger.info(
                f"Pipeline completed: run={run_id}, claim={claim_id}, "
                f"decision={result['final_decision']}, time={total_time_ms:.0f}ms"
            )

            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Pipeline error: {error_msg}")

            # Fail pipeline in state manager
            await state_manager.fail_pipeline(
                run_id=run_id,
                error=error_msg,
            )

            # Publish pipeline failed
            await event_publisher.publish_pipeline_failed(
                run_id=run_id,
                claim_id=claim_id,
                error=error_msg,
            )

            return {
                "success": False,
                "run_id": run_id,
                "claim_id": claim_id,
                "status": "failed",
                "error": error_msg,
            }

    # =========================================================================
    # STEP-BY-STEP PROCESSING METHODS (for manual trigger flow)
    # =========================================================================

    async def process_through_bronze(self, run_id: str) -> dict[str, Any]:
        """
        Process a pending claim through Router and Bronze stages only.

        This is used for manual step-by-step processing.
        After completion, claim waits for user to trigger Silver.
        """
        try:
            # Get existing pipeline state
            state = await state_manager.get_pipeline_state(run_id)
            if not state:
                raise ValueError(f"Pipeline run {run_id} not found")

            claim_id = state.claim_id
            claim_data = state.claim_data

            # Update status to running
            await state_manager.update_pipeline_state(
                run_id,
                status=PipelineStatus.RUNNING,
            )

            # Publish pipeline started
            await event_publisher.publish_pipeline_started(
                run_id=run_id,
                claim_id=claim_id,
                claim_data=claim_data,
            )

            # Create graph state
            graph_state = MedallionPipelineState(
                run_id=run_id,
                claim_id=claim_id,
                claim_data=claim_data,
                started_at=datetime.utcnow(),
            )

            # Run Router
            router_result = await self._router_node(graph_state)
            graph_state.router_output = router_result.get("router_output")
            graph_state.complexity = router_result.get("complexity", "medium")

            # Run Bronze
            bronze_result = await self._bronze_node(graph_state)
            bronze_output = bronze_result.get("bronze_output")

            # Update state - paused after bronze
            await state_manager.update_pipeline_state(
                run_id,
                current_stage=PipelineStage.BRONZE,
                status=PipelineStatus.PENDING,  # Back to pending, waiting for Silver
                bronze_output=bronze_output,
                complexity=graph_state.complexity,
            )

            logger.info(f"Bronze complete for {run_id}, waiting for Silver trigger")

            return {
                "success": True,
                "run_id": run_id,
                "claim_id": claim_id,
                "status": "pending_silver",
                "current_stage": "bronze",
                "bronze_output": bronze_output,
                "next_action": "process_silver",
            }

        except Exception as e:
            logger.error(f"process_through_bronze error: {e}")
            await state_manager.fail_pipeline(run_id, str(e))
            return {"success": False, "error": str(e)}

    async def process_silver_only(self, run_id: str) -> dict[str, Any]:
        """
        Process Silver stage only for a claim that completed Bronze.

        After completion, claim waits for user to trigger Gold.
        """
        try:
            # Get existing pipeline state
            state = await state_manager.get_pipeline_state(run_id)
            if not state:
                raise ValueError(f"Pipeline run {run_id} not found")

            claim_id = state.claim_id

            # Update status to running
            await state_manager.update_pipeline_state(
                run_id,
                status=PipelineStatus.RUNNING,
            )

            # Create graph state with existing data
            graph_state = MedallionPipelineState(
                run_id=run_id,
                claim_id=claim_id,
                claim_data=state.claim_data,
                bronze_output=state.bronze_output,
            )

            # Run Silver
            silver_result = await self._silver_node(graph_state)
            silver_output = silver_result.get("silver_output")

            # Update state - paused after silver
            await state_manager.update_pipeline_state(
                run_id,
                current_stage=PipelineStage.SILVER,
                status=PipelineStatus.PENDING,  # Back to pending, waiting for Gold
                silver_output=silver_output,
            )

            logger.info(f"Silver complete for {run_id}, waiting for Gold trigger")

            return {
                "success": True,
                "run_id": run_id,
                "claim_id": claim_id,
                "status": "pending_gold",
                "current_stage": "silver",
                "silver_output": silver_output,
                "next_action": "process_gold",
            }

        except Exception as e:
            logger.error(f"process_silver_only error: {e}")
            await state_manager.fail_pipeline(run_id, str(e))
            return {"success": False, "error": str(e)}

    async def process_gold_only(self, run_id: str) -> dict[str, Any]:
        """
        Process Gold stage only for a claim that completed Silver.

        After completion, pipeline is fully complete.
        """
        try:
            # Get existing pipeline state
            state = await state_manager.get_pipeline_state(run_id)
            if not state:
                raise ValueError(f"Pipeline run {run_id} not found")

            claim_id = state.claim_id
            start_time = state.started_at or datetime.utcnow()

            # Update status to running
            await state_manager.update_pipeline_state(
                run_id,
                status=PipelineStatus.RUNNING,
            )

            # Create graph state with existing data
            graph_state = MedallionPipelineState(
                run_id=run_id,
                claim_id=claim_id,
                claim_data=state.claim_data,
                bronze_output=state.bronze_output,
                silver_output=state.silver_output,
            )

            # Run Gold
            gold_result = await self._gold_node(graph_state)
            gold_output = gold_result.get("gold_output")

            # Calculate total processing time
            end_time = datetime.utcnow()
            total_time_ms = (end_time - start_time).total_seconds() * 1000

            # Complete pipeline
            final_decision = gold_output.get("final_decision", "unknown") if gold_output else "unknown"
            fraud_score = gold_output.get("fraud_score", 0.0) if gold_output else 0.0
            risk_level = gold_output.get("risk_level", "unknown") if gold_output else "unknown"
            insights = gold_output.get("insights", []) if gold_output else []

            await state_manager.complete_pipeline(
                run_id=run_id,
                final_decision=final_decision,
                fraud_score=fraud_score,
                risk_level=risk_level,
                insights=insights,
            )

            # Store gold output
            await state_manager.set_layer_output(run_id, "gold", gold_output)

            # Publish pipeline completed
            await event_publisher.publish_pipeline_completed(
                run_id=run_id,
                claim_id=claim_id,
                processing_time_ms=total_time_ms,
                final_decision=final_decision,
                summary={
                    "fraud_score": fraud_score,
                    "risk_level": risk_level,
                },
            )

            logger.info(f"Pipeline complete for {run_id}: {final_decision}")

            return {
                "success": True,
                "run_id": run_id,
                "claim_id": claim_id,
                "status": "completed",
                "current_stage": "gold",
                "gold_output": gold_output,
                "final_decision": final_decision,
                "fraud_score": fraud_score,
                "risk_level": risk_level,
                "total_processing_time_ms": total_time_ms,
            }

        except Exception as e:
            logger.error(f"process_gold_only error: {e}")
            await state_manager.fail_pipeline(run_id, str(e))
            return {"success": False, "error": str(e)}


# Create singleton instance
medallion_pipeline = MedallionPipeline()
