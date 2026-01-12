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

You are an experienced claims processor who knows how to spot fraud and duplicates early.
Your PRIMARY job is to catch problems BEFORE they go further - duplicates, velocity abuse, and data issues.

## ⚠️ CRITICAL: CHECK DUPLICATES AND VELOCITY FIRST!

Before ANY other validation, you MUST:

1. **CALL get_historical_claims(customer_id=<customer_id>)** to get customer's claim history
2. **CHECK FOR DUPLICATES** in the returned claims:
   - Same pet + same diagnosis within 24 hours = REJECT as duplicate
   - Same exact claim amount within 1 hour = REJECT as duplicate
   - Same provider + same day = FLAG for review
3. **CHECK VELOCITY** (claim frequency):
   - 5+ claims from same customer in 30 days = FLAG as suspicious
   - 3+ claims for same pet in 30 days = FLAG as suspicious
   - Same diagnosis repeated 3+ times = FLAG as pattern

If you find duplicates or velocity issues, QUARANTINE or REJECT immediately with detailed explanation.

## Your Responsibilities (In Order):

### Step 1: DUPLICATE & VELOCITY CHECK (MANDATORY FIRST)
- Call get_historical_claims with customer_id
- Compare this claim against recent history
- Look for: exact duplicates, similar claims, high frequency
- If duplicate found: REJECT with "DUPLICATE: [reason]"
- If velocity issue: QUARANTINE with "VELOCITY: [reason]"

### Step 2: SCHEMA VALIDATION
- Required fields: claim_id, policy_id, customer_id, claim_amount
- Validate data types and formats
- Use get_policy to verify policy exists and is active
- Use verify_provider to check provider is valid

### Step 3: ANOMALY DETECTION
- Unusual claim amounts (too high, round numbers)
- Statistical outliers vs customer history
- Suspicious patterns

### Step 4: DATA CLEANING
- Use validate_diagnosis_code to standardize codes
- Fix date formats
- Normalize provider names

### Step 5: QUALITY ASSESSMENT
- Calculate completeness score
- Identify data gaps

### Step 6: DECISION
- ACCEPT: Data is valid, no duplicates, reasonable velocity
- QUARANTINE: Has issues needing review (velocity warning, minor anomalies)
- REJECT: Invalid data, duplicate claim, or fraud indicators

## Available Tools:

- **get_historical_claims(customer_id)**: GET CUSTOMER HISTORY - USE THIS FIRST!
- get_policy(policy_id): Get policy details and status
- verify_provider(provider_id): Verify provider exists
- validate_diagnosis_code(code): Validate diagnosis codes
- validate_schema(claim_data): Check schema validity
- detect_anomalies(claim_data): Find statistical anomalies
- clean_data(claim_data): Normalize data
- assess_quality(claim_data): Rate data quality

## Example Duplicate Detection:

If customer CUST-001 submits claim for pet PET-001 with diagnosis "chocolate toxicity"
and get_historical_claims returns a claim from 2 hours ago with same pet and diagnosis:
→ REJECT: "DUPLICATE: Same pet (PET-001) with same diagnosis (chocolate toxicity) submitted 2 hours ago"

## Example Velocity Detection:

If get_historical_claims shows customer has 6 claims in last 30 days:
→ QUARANTINE: "VELOCITY: Customer has 6 claims in 30 days (threshold: 5). Review for potential abuse."

## UI Card Display (REQUIRED):

At the END of your response, include a JSON block for the UI card display:

```card_display
{
  "title": "Bronze Layer",
  "subtitle": "AI Data Validation Agent",
  "primary_metric": {"label": "Data Quality", "value": "95%"},
  "secondary_metrics": [
    {"label": "Completeness", "value": "100%"},
    {"label": "Duplicates Found", "value": "0"},
    {"label": "Customer Claims (30d)", "value": "3"}
  ],
  "status": "Accepted",
  "status_color": "green",
  "alerts": ["List any warnings or flags here"],
  "summary": "Brief 1-sentence summary of what you found"
}
```

Status colors: green=accept, yellow=quarantine, red=reject

Always call write_bronze at the end to save results."""


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

            # Create input message - emphasize duplicate/velocity check first
            customer_id = claim_data.get("customer_id", "unknown")
            pet_id = claim_data.get("pet_id", "unknown")
            
            input_message = f"""Process this pet insurance claim. CHECK FOR DUPLICATES FIRST!

## Claim Details
- Claim ID: {claim_id}
- Customer ID: {customer_id}
- Pet ID: {pet_id}

```json
{json.dumps(claim_data, indent=2)}
```

## MANDATORY Steps (in this exact order):

### Step 1: DUPLICATE & VELOCITY CHECK (DO THIS FIRST!)
Call get_historical_claims(customer_id="{customer_id}") to get this customer's claim history.
Then check:
- Is there a claim with same pet_id and similar diagnosis in the last 24 hours? → REJECT as duplicate
- Is there a claim with exact same amount in the last hour? → REJECT as duplicate  
- How many claims has this customer submitted in the last 30 days? → If 5+, FLAG velocity issue
- How many claims for pet "{pet_id}" in the last 30 days? → If 3+, FLAG velocity issue

### Step 2: Schema Validation
Use validate_schema to check required fields.

### Step 3: Anomaly Detection  
Use detect_anomalies to find statistical outliers.

### Step 4: Data Cleaning
Use clean_data to normalize the data.

### Step 5: Quality Assessment
Use assess_quality to rate data quality.

### Step 6: Final Decision
Call write_bronze with your decision:
- REJECT: If duplicate found or critical issues
- QUARANTINE: If velocity warnings or anomalies need review
- ACCEPT: If all checks pass

Remember: Catching duplicates early saves everyone time and money!"""

            # Publish step events
            await events.start_step("Duplicate & Velocity Check")
            await events.reason(
                f"Checking customer {customer_id} claim history for duplicates and velocity issues",
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
            "card_display": None,  # AI-generated card display
        }

        # Parse through messages to extract tool results and final response
        for msg in messages:
            if hasattr(msg, "content") and isinstance(msg.content, str):
                content = msg.content.lower()
                original_content = msg.content

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

                        # Extract card_display JSON block
                        card_display = self._extract_card_display(original_content)
                        if card_display:
                            result["card_display"] = card_display

        # Generate fallback card_display if AI didn't provide one
        if not result["card_display"]:
            result["card_display"] = self._generate_fallback_card(result)

        return result

    def _extract_card_display(self, content: str) -> Optional[dict]:
        """Extract card_display JSON from AI response."""
        import re

        # Look for ```card_display ... ``` block
        pattern = r'```card_display\s*\n?(.*?)\n?```'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                logger.warning("Failed to parse card_display JSON")

        # Fallback: look for any JSON with card_display structure
        pattern2 = r'\{[^{}]*"title"[^{}]*"subtitle"[^{}]*\}'
        match2 = re.search(pattern2, content, re.DOTALL)
        if match2:
            try:
                return json.loads(match2.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _generate_fallback_card(self, result: dict) -> dict:
        """Generate fallback card display if AI didn't provide one."""
        quality_pct = int(result.get("quality_score", 0.8) * 100)
        decision = result.get("decision", "accept")

        status_map = {
            "accept": ("Accepted", "green"),
            "quarantine": ("Quarantined", "yellow"),
            "reject": ("Rejected", "red"),
        }
        status, color = status_map.get(decision, ("Processed", "blue"))

        return {
            "title": "Bronze Layer",
            "subtitle": "AI Data Validation Agent",
            "primary_metric": {"label": "Data Quality", "value": f"{quality_pct}%"},
            "secondary_metrics": [
                {"label": "Confidence", "value": f"{int(result.get('confidence', 0.85) * 100)}%"}
            ],
            "status": status,
            "status_color": color,
            "summary": result.get("reasoning", "Data validation completed.")[:100]
        }


# Create singleton instance
bronze_agent = BronzeAgent()
