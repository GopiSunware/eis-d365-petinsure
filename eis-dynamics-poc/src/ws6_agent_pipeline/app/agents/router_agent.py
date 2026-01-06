"""
Router Agent for pipeline orchestration.

This agent determines claim complexity and routes claims
to the appropriate processing path.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from ..config import settings
from ..orchestration.events import event_publisher
from ..orchestration.state import state_manager

logger = logging.getLogger(__name__)


class ClaimComplexityResult(BaseModel):
    """Result of claim complexity assessment."""
    complexity: str = "medium"  # simple, medium, complex
    reasoning: str = ""
    factors: list[str] = Field(default_factory=list)
    processing_path: str = "standard"  # fast_track, standard, enhanced
    estimated_time_ms: int = 10000


class RouterAgent:
    """
    Router Agent for claim complexity assessment and routing.

    Analyzes incoming claims and determines the appropriate
    processing path based on complexity factors.
    """

    def __init__(self):
        self.name = "router"

        # Complexity thresholds
        self.amount_thresholds = {
            "simple": 1000,
            "medium": 10000,
            "complex": float("inf"),
        }

        # High-risk claim types
        self.complex_claim_types = ["emergency", "surgery", "hospitalization"]

        # Standard claim types
        self.simple_claim_types = ["wellness", "routine", "vaccination"]

    async def assess_complexity(
        self,
        claim_data: dict[str, Any],
    ) -> ClaimComplexityResult:
        """
        Assess claim complexity based on multiple factors.

        Args:
            claim_data: Raw claim data to assess

        Returns:
            ClaimComplexityResult with complexity level and reasoning
        """
        result = ClaimComplexityResult()
        factors = []

        # Factor 1: Claim amount
        claim_amount = float(claim_data.get("claim_amount", 0))
        if claim_amount < self.amount_thresholds["simple"]:
            factors.append(f"Low claim amount (${claim_amount:,.2f})")
            amount_complexity = "simple"
        elif claim_amount < self.amount_thresholds["medium"]:
            factors.append(f"Medium claim amount (${claim_amount:,.2f})")
            amount_complexity = "medium"
        else:
            factors.append(f"High claim amount (${claim_amount:,.2f})")
            amount_complexity = "complex"

        # Factor 2: Claim type
        claim_type = str(claim_data.get("claim_type", "accident")).lower()
        if claim_type in self.simple_claim_types:
            factors.append(f"Simple claim type ({claim_type})")
            type_complexity = "simple"
        elif claim_type in self.complex_claim_types:
            factors.append(f"Complex claim type ({claim_type})")
            type_complexity = "complex"
        else:
            factors.append(f"Standard claim type ({claim_type})")
            type_complexity = "medium"

        # Factor 3: Diagnosis code presence and format
        diagnosis_code = claim_data.get("diagnosis_code", "")
        if not diagnosis_code:
            factors.append("Missing diagnosis code")
            diagnosis_complexity = "medium"
        elif diagnosis_code.startswith("C"):  # Cancer/oncology codes
            factors.append(f"Complex diagnosis category ({diagnosis_code})")
            diagnosis_complexity = "complex"
        else:
            factors.append(f"Standard diagnosis ({diagnosis_code})")
            diagnosis_complexity = "simple"

        # Factor 4: Data completeness
        required_fields = ["claim_id", "policy_id", "customer_id", "claim_amount"]
        optional_fields = ["diagnosis_code", "treatment_date", "provider_name"]

        missing_required = sum(1 for f in required_fields if not claim_data.get(f))
        missing_optional = sum(1 for f in optional_fields if not claim_data.get(f))

        if missing_required > 0:
            factors.append(f"Missing {missing_required} required field(s)")
            completeness_complexity = "complex"
        elif missing_optional > 1:
            factors.append(f"Missing {missing_optional} optional field(s)")
            completeness_complexity = "medium"
        else:
            factors.append("Data completeness: Good")
            completeness_complexity = "simple"

        # Determine overall complexity
        complexities = [amount_complexity, type_complexity, diagnosis_complexity, completeness_complexity]
        if "complex" in complexities:
            result.complexity = "complex"
            result.processing_path = "enhanced"
            result.estimated_time_ms = 20000
        elif complexities.count("medium") >= 2:
            result.complexity = "medium"
            result.processing_path = "standard"
            result.estimated_time_ms = 12000
        else:
            result.complexity = "simple"
            result.processing_path = "fast_track"
            result.estimated_time_ms = 8000

        result.factors = factors
        result.reasoning = f"Claim classified as {result.complexity} based on: {', '.join(factors)}"

        return result

    async def route(
        self,
        run_id: str,
        claim_id: str,
        claim_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Route a claim based on complexity assessment.

        Args:
            run_id: Pipeline run ID
            claim_id: Claim identifier
            claim_data: Raw claim data to route

        Returns:
            Routing decision with complexity and processing path
        """
        start_time = datetime.utcnow()

        try:
            # Publish agent started
            await event_publisher.publish_agent_started(
                run_id=run_id,
                claim_id=claim_id,
                agent_name=self.name,
                total_steps=1,
            )

            # Update state manager
            await state_manager.start_agent(run_id, self.name, total_steps=1)

            # Assess complexity
            complexity_result = await self.assess_complexity(claim_data)

            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time_ms = (end_time - start_time).total_seconds() * 1000

            result = {
                "success": True,
                "claim_id": claim_id,
                "complexity": complexity_result.complexity,
                "processing_path": complexity_result.processing_path,
                "estimated_time_ms": complexity_result.estimated_time_ms,
                "factors": complexity_result.factors,
                "reasoning": complexity_result.reasoning,
                "processing_time_ms": processing_time_ms,
            }

            # Update state manager
            await state_manager.complete_agent(
                run_id=run_id,
                agent_name=self.name,
                output=result,
            )

            # Update pipeline state with complexity
            await state_manager.update_pipeline_state(
                run_id=run_id,
                complexity=complexity_result.complexity,
            )

            # Publish agent completed
            await event_publisher.publish_agent_completed(
                run_id=run_id,
                claim_id=claim_id,
                agent_name=self.name,
                processing_time_ms=processing_time_ms,
                output_summary={
                    "complexity": complexity_result.complexity,
                    "processing_path": complexity_result.processing_path,
                },
            )

            # Publish reasoning event
            await event_publisher.publish_reasoning(
                run_id=run_id,
                claim_id=claim_id,
                agent_name=self.name,
                step_name="complexity_assessment",
                reasoning=complexity_result.reasoning,
                reasoning_type="decision",
            )

            logger.info(
                f"Router Agent completed: claim={claim_id}, "
                f"complexity={complexity_result.complexity}, "
                f"path={complexity_result.processing_path}"
            )

            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Router Agent error: {error_msg}")

            # Update state manager with error
            await state_manager.fail_agent(
                run_id=run_id,
                agent_name=self.name,
                error=error_msg,
            )

            # Publish error event
            await event_publisher.publish_agent_failed(
                run_id=run_id,
                claim_id=claim_id,
                agent_name=self.name,
                error=error_msg,
            )

            # Return default routing on error
            return {
                "success": False,
                "claim_id": claim_id,
                "complexity": "medium",
                "processing_path": "standard",
                "error": error_msg,
            }


# Create singleton instance
router_agent = RouterAgent()
