"""
Bronze Agent for data validation and cleaning.

This agent handles the Bronze layer of the medallion architecture:
- Schema validation
- Anomaly detection
- Data cleaning and normalization
- Quality assessment
- Accept/Quarantine/Reject decisions
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from ..config import settings
from ..orchestration.events import EventContext, event_publisher
from ..orchestration.state import state_manager
from ..tools import (
    BRONZE_VALIDATION_TOOLS,
    write_bronze,
)
from ..tools.storage_tools import get_historical_claims
# Import unified API tools for Bronze layer (policy/provider validation)
from ..tools import (
    UNIFIED_API_BRONZE_TOOLS,
    get_policy,
    verify_provider,
    validate_diagnosis_code,
)

logger = logging.getLogger(__name__)


# Bronze Agent System Prompt
BRONZE_AGENT_PROMPT = """You are a Bronze Layer Data Agent for pet insurance claims processing.

Your role is to validate, clean, and assess incoming claim data before it moves to the Silver layer.

## Your Responsibilities:

1. **VALIDATE**: Check all required fields are present and correctly typed
   - Required fields: claim_id, policy_id, customer_id, claim_amount
   - Validate data types and formats
   - Flag missing or invalid data
   - Use get_policy to verify policy exists and is active
   - Use verify_provider to check provider is valid

2. **DETECT ANOMALIES**: Look for suspicious patterns
   - Check for duplicate claims
   - Identify unusual claim amounts
   - Flag statistical outliers

3. **CLEAN**: Normalize and fix data issues
   - Use validate_diagnosis_code to standardize codes
   - Fix date formats
   - Normalize provider names

4. **ASSESS QUALITY**: Rate the overall data quality
   - Calculate completeness score
   - Identify data gaps
   - Provide quality metrics

5. **DECIDE**: Make a decision about this claim
   - ACCEPT: Data is valid and ready for Silver layer
   - QUARANTINE: Data has issues that need review
   - REJECT: Data is invalid and cannot be processed

## Available Tools (Unified API - Port 8000):

- get_policy(policy_id): Get policy details and status
- verify_provider(provider_id): Verify provider exists and is valid
- validate_diagnosis_code(code): Validate and get diagnosis code details
- check_policy_limits(policy_id): Check coverage limits and usage
- get_waiting_periods(policy_id): Get waiting period status

## Guidelines:

- Always explain your reasoning step by step
- Be thorough but efficient
- Provide confidence scores for your decisions
- Include specific details about any issues found

## Output Format:

After using the tools to analyze the data, provide:
1. A summary of validation results
2. Any anomalies or concerns found
3. Data cleaning actions taken
4. Quality assessment scores
5. Your final decision with confidence and reasoning

Always call the write_bronze tool at the end to save the results."""


class BronzeAgent:
    """
    Bronze Layer Agent using LangGraph.

    Validates, cleans, and assesses incoming claim data.
    """

    def __init__(self):
        self.name = "bronze"
        # Combine legacy validation tools with new unified API tools
        self.tools = (
            BRONZE_VALIDATION_TOOLS +
            UNIFIED_API_BRONZE_TOOLS +
            [write_bronze, get_historical_claims]
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
            prompt=BRONZE_AGENT_PROMPT,
        )

    async def process(
        self,
        run_id: str,
        claim_id: str,
        claim_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Process a claim through the Bronze Agent.

        Args:
            run_id: Pipeline run ID
            claim_id: Claim identifier
            claim_data: Raw claim data to process

        Returns:
            Bronze layer processing results
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
                total_steps=5,
            )

            # Update state manager
            await state_manager.start_agent(run_id, self.name, total_steps=5)

            # Create input message
            input_message = f"""Please process the following pet insurance claim:

Claim ID: {claim_id}
Claim Data:
```json
{json.dumps(claim_data, indent=2)}
```

Steps to follow:
1. First, validate the schema using validate_schema
2. Then, detect any anomalies using detect_anomalies
3. Clean the data using clean_data
4. Assess quality using assess_quality
5. Finally, write to bronze layer with your decision using write_bronze

Please analyze this claim and make a decision (ACCEPT, QUARANTINE, or REJECT).
Explain your reasoning throughout the process."""

            # Publish step events
            await events.start_step("Schema Validation")
            await events.reason(
                f"Starting validation of claim {claim_id}",
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
            result = self._extract_results(result_state, claim_data)
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
                    "decision": result.get("decision", "unknown"),
                    "confidence": result.get("confidence", 0),
                    "quality_score": result.get("quality_score", 0),
                },
            )

            # Publish decision
            await events.decide(
                decision=result.get("decision", "unknown"),
                confidence=result.get("confidence", 0),
                reasoning=result.get("reasoning", ""),
                decision_type="validation",
            )

            logger.info(
                f"Bronze Agent completed: claim={claim_id}, "
                f"decision={result.get('decision')}, "
                f"time={processing_time_ms:.0f}ms"
            )

            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Bronze Agent error: {error_msg}")

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
                "decision": "error",
            }

    def _extract_results(
        self,
        state: dict,
        original_claim_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract structured results from the agent's final state."""
        messages = state.get("messages", [])

        # Default result
        result = {
            "success": True,
            "claim_id": original_claim_data.get("claim_id"),
            "decision": "accept",
            "confidence": 0.85,
            "reasoning": "",
            "validation_result": {},
            "anomaly_result": {},
            "cleaning_result": {},
            "quality_result": {},
            "quality_score": 0.8,
            "cleaned_data": original_claim_data,
        }

        # Parse through messages to extract tool results and final response
        for msg in messages:
            if hasattr(msg, "content") and isinstance(msg.content, str):
                content = msg.content.lower()

                # Extract decision from content
                if "reject" in content:
                    result["decision"] = "reject"
                    result["confidence"] = 0.9
                elif "quarantine" in content:
                    result["decision"] = "quarantine"
                    result["confidence"] = 0.85
                elif "accept" in content:
                    result["decision"] = "accept"
                    result["confidence"] = 0.9

                # Use last AI message as reasoning
                if isinstance(msg, AIMessage):
                    if not hasattr(msg, "tool_calls") or not msg.tool_calls:
                        result["reasoning"] = msg.content[:500]  # Truncate if too long

        return result


# Create singleton instance
bronze_agent = BronzeAgent()
