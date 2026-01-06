"""
Gold Agent for analytics and insights.

This agent handles the Gold layer of the medallion architecture:
- Risk and fraud assessment
- Insight generation
- KPI calculation
- Alert creation
- Customer 360 updates
- Final processing decisions
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
    GOLD_ANALYTICS_TOOLS,
    write_gold,
)
from ..tools.storage_tools import update_kpi_aggregates
# Import unified API tools for Gold layer (fraud detection & analytics)
from ..tools import (
    UNIFIED_API_GOLD_TOOLS,
    # Critical fraud detection tools
    check_fraud_indicators,
    velocity_check,
    duplicate_check,
    fraud_pattern_match,
    provider_customer_analysis,
    calculate_fraud_score,
    # Provider analytics
    get_provider_fraud_rate,
    get_provider_peer_comparison,
    # Customer analytics
    get_customer_risk_tier,
    get_customer_ltv,
    # Billing analytics
    get_annual_summary,
)

logger = logging.getLogger(__name__)


# Gold Agent System Prompt
GOLD_AGENT_PROMPT = """You are a Gold Layer Analytics Agent for pet insurance claims processing.

Your role is to generate business insights, assess risk, and make final processing decisions.
**CRITICAL**: You have access to fraud detection tools that can identify patterns rule-based systems miss.

## Your Responsibilities:

1. **ASSESS FRAUD** (CRITICAL - Use Unified API tools):
   - **check_fraud_indicators**: Main fraud detection - ALWAYS CALL THIS FIRST
   - **velocity_check**: Check claim frequency patterns
   - **duplicate_check**: Find similar claims
   - **fraud_pattern_match**: Match against known fraud patterns
   - **provider_customer_analysis**: Check provider-customer relationships
   - **calculate_fraud_score**: Get comprehensive fraud score

2. **PROVIDER ANALYSIS**:
   - Use get_provider_fraud_rate to check provider's fraud history
   - Use get_provider_peer_comparison to compare to other providers

3. **CUSTOMER ANALYTICS**:
   - Use get_customer_risk_tier for customer risk level
   - Use get_customer_ltv for lifetime value analysis
   - Use get_annual_summary for billing overview

4. **GENERATE INSIGHTS**: Extract business intelligence
   - Identify customer patterns and trends
   - Spot anomalies in claim patterns
   - Generate actionable recommendations

5. **MAKE FINAL DECISION**: Determine processing path
   - AUTO_APPROVE: Low risk (fraud score <25), amount ≤$500, in-network
   - STANDARD_REVIEW: Medium risk (25-49) or regular claims
   - MANUAL_REVIEW: High risk (50-74) - needs adjuster
   - INVESTIGATION: Critical risk (≥75) - escalate to fraud unit

## Available Fraud Detection Tools (Unified API - Port 8000):

**Primary Fraud Tools (USE THESE):**
- check_fraud_indicators(customer_id, pet_id, provider_id, claim_amount, diagnosis_code, service_date)
  → Returns fraud_score, risk_level, indicators[], recommendation
- velocity_check(customer_id, days=30): Check recent claim frequency
- duplicate_check(customer_id, claim_amount, diagnosis_code, tolerance_days=30): Find similar claims
- fraud_pattern_match(customer_id, pet_id, provider_id): Match against known patterns:
  * PATTERN_1: Chronic Condition Gaming (pre-existing conditions claimed as accidents)
  * PATTERN_2: Provider Collusion (exclusive out-of-network provider use)
  * PATTERN_3: Staged Timing (claims just after waiting period)
- calculate_fraud_score(customer_id, pet_id, provider_id, claim_amount, diagnosis_code, service_date)

**Provider Analytics:**
- get_provider_fraud_rate(provider_id): Provider's fraud claim percentage
- get_provider_peer_comparison(provider_id): Compare to peers

## FRAUD PATTERNS TO DETECT:

1. **Chronic Condition Gaming** (e.g., CUST-023):
   - Pet has documented pre-existing condition (hip dysplasia)
   - Multiple "accident" claims all involve same body area
   - Rule-based systems approve because each claim is under threshold
   - YOU should recognize the pattern across claims

2. **Provider Collusion** (e.g., CUST-067):
   - Customer exclusively uses one out-of-network provider
   - Claims consistently just under review thresholds ($4,700-$4,900)
   - High frequency with suspicious timing
   - YOU should flag the concentration and limit optimization

3. **Staged Timing** (e.g., CUST-089):
   - Claim filed just days after waiting period ends
   - Condition typical for breed (French Bulldog + IVDD)
   - Statistical anomaly in timing
   - YOU should recognize the timing is suspicious

## Business Analyst Mindset:

Think like a fraud investigator:
- What patterns emerge when looking at claim history?
- Is this provider suspicious?
- Does the timing make sense biologically?
- Are there pre-existing conditions being masked as accidents?

## Guidelines:

- **ALWAYS** call check_fraud_indicators first
- Provide ACTIONABLE insights with clear reasoning
- Quantify risks and opportunities when possible
- Be specific about WHY you flagged something

## Output Format:

After analysis:
1. Fraud assessment with score and specific indicators
2. Pattern matches found (if any)
3. Risk assessment with level
4. Key insights discovered
5. Final decision with confidence and full reasoning

Always call write_gold at the end to save the analytics record."""


class GoldAgent:
    """
    Gold Layer Agent using LangGraph.

    Performs analytics, risk assessment, and generates insights.
    """

    def __init__(self):
        self.name = "gold"
        # Combine legacy analytics tools with new unified API tools
        # Fraud detection tools are CRITICAL for the demo
        self.tools = (
            GOLD_ANALYTICS_TOOLS +
            UNIFIED_API_GOLD_TOOLS +
            [write_gold, update_kpi_aggregates]
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
            prompt=GOLD_AGENT_PROMPT,
        )

    async def process(
        self,
        run_id: str,
        claim_id: str,
        silver_data: dict[str, Any],
        total_processing_time_ms: float = 0.0,
    ) -> dict[str, Any]:
        """
        Process Silver layer output through the Gold Agent.

        Args:
            run_id: Pipeline run ID
            claim_id: Claim identifier
            silver_data: Silver layer output to analyze
            total_processing_time_ms: Total time from pipeline start

        Returns:
            Gold layer processing results
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

            # Create input message
            input_message = f"""Please analyze the following Silver layer claim data and generate insights:

Claim ID: {claim_id}
Silver Data:
```json
{json.dumps(silver_data, indent=2, default=str)}
```

Total Processing Time So Far: {total_processing_time_ms:.0f}ms

Steps to follow:
1. Assess risk and fraud probability using assess_risk
2. Generate business insights using generate_insights
3. Calculate KPI metrics using calculate_kpi_metrics
4. Create any necessary alerts using create_alerts
5. Update customer 360 profile using update_customer_360
6. Write to gold layer with final decision using write_gold

Provide comprehensive analysis and a final recommendation for this claim."""

            # Publish step events
            await events.start_step("Risk Assessment")
            await events.reason(
                f"Starting risk analysis for claim {claim_id}",
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
            result = self._extract_results(result_state, silver_data)
            result["processing_time_ms"] = processing_time_ms
            result["total_pipeline_time_ms"] = total_processing_time_ms + processing_time_ms

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
                    "final_decision": result.get("final_decision", "unknown"),
                    "fraud_score": result.get("fraud_score", 0),
                    "risk_level": result.get("risk_level", "unknown"),
                    "alerts_count": result.get("alerts_count", 0),
                },
            )

            # Publish final decision
            await events.decide(
                decision=result.get("final_decision", "unknown"),
                confidence=result.get("confidence", 0),
                reasoning=result.get("reasoning", ""),
                decision_type="final",
            )

            # Publish alerts if any
            for alert in result.get("alerts", []):
                await events.alert(
                    alert_type=alert.get("type", "unknown"),
                    alert_message=alert.get("message", ""),
                    action_required=alert.get("action_required", False),
                )

            logger.info(
                f"Gold Agent completed: claim={claim_id}, "
                f"decision={result.get('final_decision')}, "
                f"fraud_score={result.get('fraud_score'):.2f}, "
                f"time={processing_time_ms:.0f}ms"
            )

            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Gold Agent error: {error_msg}")

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
                "final_decision": "error",
            }

    def _extract_results(
        self,
        state: dict,
        silver_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract structured results from the agent's final state."""
        messages = state.get("messages", [])

        # Default result
        result = {
            "success": True,
            "claim_id": silver_data.get("claim_id"),
            "silver_reference": silver_data,
            "risk_assessment": {},
            "fraud_score": 0.15,
            "risk_level": "low",
            "insights": [],
            "kpi_metrics": {},
            "alerts": [],
            "alerts_count": 0,
            "customer_360_updates": {},
            "final_decision": "auto_approve",
            "confidence": 0.85,
            "reasoning": "",
        }

        # Extract from AI messages
        for msg in messages:
            if isinstance(msg, AIMessage):
                if not hasattr(msg, "tool_calls") or not msg.tool_calls:
                    content = msg.content.lower()
                    result["reasoning"] = msg.content[:1000]

                    # Extract decision from content
                    if "investigation" in content or "critical" in content:
                        result["final_decision"] = "investigation"
                        result["risk_level"] = "critical"
                    elif "manual_review" in content or "high risk" in content:
                        result["final_decision"] = "manual_review"
                        result["risk_level"] = "high"
                    elif "standard_review" in content or "medium" in content:
                        result["final_decision"] = "standard_review"
                        result["risk_level"] = "medium"
                    else:
                        result["final_decision"] = "auto_approve"
                        result["risk_level"] = "low"

        return result


# Create singleton instance
gold_agent = GoldAgent()
