"""
Silver Agent for data enrichment and transformation.

This agent handles the Silver layer of the medallion architecture:
- Data enrichment (policy, customer, pet, provider)
- Value normalization and standardization
- Business rules validation
- Coverage calculation
- Quality scoring
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from ..config import settings
from ..orchestration.events import EventContext, event_publisher
from ..orchestration.state import state_manager
from ..tools import (
    SILVER_ENRICHMENT_TOOLS,
    write_silver,
)
# Import unified API tools for Silver layer (enrichment)
from ..tools import (
    UNIFIED_API_SILVER_TOOLS,
    get_customer,
    get_claim_history,
    get_customer_ltv,
    get_pet_profile,
    get_pet_medical_history,
    get_pet_pre_existing_conditions,
    get_provider_network_status,
    check_coverage,
    get_policy_exclusions,
    get_treatment_benchmarks,
    calculate_reimbursement,
    check_deductible_status,
)

logger = logging.getLogger(__name__)


# Silver Agent System Prompt
SILVER_AGENT_PROMPT = """You are a Silver Layer Enrichment Agent for pet insurance claims processing.

Your role is to enrich, normalize, and transform validated Bronze layer data.

## Your Responsibilities:

1. **ENRICH**: Pull in related data using Unified API (port 8000)
   - Use get_customer to fetch customer info
   - Use get_claim_history to see past claims
   - Use get_customer_ltv for lifetime value
   - Use get_pet_profile for pet details
   - Use get_pet_medical_history for health records
   - Use get_pet_pre_existing_conditions - CRITICAL for fraud detection
   - Use get_provider_network_status for network info

2. **NORMALIZE**: Standardize codes and values
   - Use get_treatment_benchmarks for typical costs
   - Map diagnosis codes to ICD-10-VET
   - Categorize claim types
   - Calculate derived fields (claim size, priority)

3. **VALIDATE BUSINESS RULES**: Apply coverage checks
   - Use check_coverage to verify diagnosis is covered
   - Use get_policy_exclusions to check exclusions
   - Use check_deductible_status for deductible info
   - Use calculate_reimbursement for expected payout

4. **CALCULATE SCORES**: Assess enriched data quality
   - Enrichment completeness score
   - Data confidence score
   - Overall silver layer score

## Available Tools (Unified API - Port 8000):

Customer Tools:
- get_customer(customer_id): Full customer profile
- get_claim_history(customer_id): All past claims
- get_customer_ltv(customer_id): Lifetime value analysis

Pet Tools:
- get_pet_profile(pet_id): Pet details and breed
- get_pet_medical_history(pet_id): Health records
- get_pet_pre_existing_conditions(pet_id): CRITICAL - Known conditions

Policy Tools:
- check_coverage(policy_id, diagnosis_code): Coverage verification
- get_policy_exclusions(policy_id): What's not covered

Billing Tools:
- calculate_reimbursement(policy_id, claim_amount, ...): Expected payout
- check_deductible_status(policy_id): Deductible met status

Medical Tools:
- get_treatment_benchmarks(diagnosis_code): Typical costs

## Context to Consider:

- Is this a repeat customer? What's their claim history?
- Is the provider in-network? What's their track record?
- Does the claim amount match typical costs for this diagnosis?
- Are there any coverage exclusions or limitations?
- **IMPORTANT**: Check pre-existing conditions - customers may claim "accidents" for chronic issues

## Guidelines:

- Always explain your enrichment decisions
- Flag any concerns or anomalies discovered during enrichment
- Provide detailed coverage calculations
- Consider the customer's overall relationship and value

## Output Format:

After using the tools to enrich and validate:
1. Summary of enrichment data found
2. Normalized values and categories
3. Business rules validation results
4. Coverage calculation breakdown
5. Quality scores and confidence

Always call write_silver at the end to save the enriched record."""


class SilverAgent:
    """
    Silver Layer Agent using LangGraph.

    Enriches, normalizes, and validates claim data.
    """

    def __init__(self):
        self.name = "silver"
        # Combine legacy enrichment tools with new unified API tools
        self.tools = (
            SILVER_ENRICHMENT_TOOLS +
            UNIFIED_API_SILVER_TOOLS +
            [write_silver]
        )
        self.llm = self._create_llm()
        self.agent = self._build_agent()

    def _create_llm(self):
        """Create the LLM based on configuration."""
        if settings.AI_PROVIDER == "claude":
            return ChatAnthropic(
                model=settings.CLAUDE_MODEL,
                api_key=settings.ANTHROPIC_API_KEY,
                temperature=settings.AGENT_TEMPERATURE,
                max_tokens=4096,
            )
        else:
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                api_key=settings.OPENAI_API_KEY,
                temperature=settings.AGENT_TEMPERATURE,
            )

    def _build_agent(self):
        """Build the LangGraph react agent."""
        return create_react_agent(
            self.llm,
            self.tools,
            prompt=SILVER_AGENT_PROMPT,
        )

    async def process(
        self,
        run_id: str,
        claim_id: str,
        bronze_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Process Bronze layer output through the Silver Agent.

        Args:
            run_id: Pipeline run ID
            claim_id: Claim identifier
            bronze_data: Bronze layer output to enrich

        Returns:
            Silver layer processing results
        """
        start_time = datetime.utcnow()

        # Create event context
        events = EventContext(
            publisher=event_publisher,
            run_id=run_id,
            claim_id=claim_id,
            agent_name=self.name,
        )

        try:
            # Publish agent started
            await event_publisher.publish_agent_started(
                run_id=run_id,
                claim_id=claim_id,
                agent_name=self.name,
                total_steps=6,
            )

            # Update state manager
            await state_manager.start_agent(run_id, self.name, total_steps=6)

            # Extract raw claim data from bronze output
            claim_data = bronze_data.get("cleaned_data", bronze_data.get("raw_data", bronze_data))

            # Create input message
            input_message = f"""Please enrich and validate the following Bronze layer claim data:

Claim ID: {claim_id}
Bronze Data:
```json
{json.dumps(bronze_data, indent=2, default=str)}
```

Steps to follow:
1. Enrich the claim with policy, customer, pet, and provider data using enrich_claim
2. Get customer claim history using get_customer_claim_history
3. Normalize values and diagnosis codes using normalize_values
4. Apply business rules for coverage validation using apply_business_rules
5. Calculate quality scores using calculate_quality_scores
6. Write to silver layer using write_silver

Provide detailed reasoning about the enrichment and any concerns found."""

            # Publish step events
            await events.start_step("Data Enrichment")
            await events.reason(
                f"Starting enrichment of claim {claim_id} from Bronze layer",
                reasoning_type="analysis"
            )

            # Run the agent
            result_state = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=input_message)]},
                config={"recursion_limit": 25},
            )

            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time_ms = (end_time - start_time).total_seconds() * 1000

            # Extract results from final state
            result = self._extract_results(result_state, bronze_data)
            result["processing_time_ms"] = processing_time_ms

            # Update state manager
            await state_manager.complete_agent(
                run_id=run_id,
                agent_name=self.name,
                output=result,
            )

            # Publish agent completed
            await event_publisher.publish_agent_completed(
                run_id=run_id,
                claim_id=claim_id,
                agent_name=self.name,
                processing_time_ms=processing_time_ms,
                output_summary={
                    "is_covered": result.get("is_covered", True),
                    "expected_reimbursement": result.get("expected_reimbursement", 0),
                    "quality_score": result.get("quality_score", 0),
                },
            )

            logger.info(
                f"Silver Agent completed: claim={claim_id}, "
                f"covered={result.get('is_covered')}, "
                f"time={processing_time_ms:.0f}ms"
            )

            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Silver Agent error: {error_msg}")

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

            return {
                "success": False,
                "error": error_msg,
                "claim_id": claim_id,
            }

    def _extract_results(
        self,
        state: dict,
        bronze_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract structured results from the agent's final state."""
        messages = state.get("messages", [])
        claim_data = bronze_data.get("cleaned_data", bronze_data.get("raw_data", bronze_data))

        # Default result
        result = {
            "success": True,
            "claim_id": claim_data.get("claim_id"),
            "bronze_reference": bronze_data,
            "enrichment_data": {},
            "normalized_data": {},
            "business_rules_result": {},
            "is_covered": True,
            "expected_reimbursement": 0.0,
            "coverage_percentage": 80.0,
            "quality_score": 0.85,
            "enrichment_notes": "",
        }

        # Extract reasoning from AI messages
        for msg in messages:
            if isinstance(msg, AIMessage):
                if not hasattr(msg, "tool_calls") or not msg.tool_calls:
                    result["enrichment_notes"] = msg.content[:500]

        # Calculate expected reimbursement
        claim_amount = float(claim_data.get("claim_amount", 0))
        result["expected_reimbursement"] = claim_amount * 0.8  # Default 80% reimbursement

        return result


# Create singleton instance
silver_agent = SilverAgent()
