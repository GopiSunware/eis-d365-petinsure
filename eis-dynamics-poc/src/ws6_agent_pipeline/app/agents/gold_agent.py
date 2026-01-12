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


# Gold Agent System Prompt - Smart Tiered Approach
GOLD_AGENT_PROMPT = """You are a Gold Layer Analytics Agent for pet insurance claims.

## CRITICAL RULES

### Rule 1: THINK OUT LOUD
Before EVERY tool call, write:
"🔍 THINKING: I am calling [tool_name] because [specific reason]"

### Rule 2: CHECK PREVIOUS LAYERS FIRST
Read Bronze and Silver results. Look for RED FLAGS:
- Bronze anomaly_score > 0.3 → Suspicious
- Bronze decision = "quarantine" → Needs investigation
- Silver status_color = "yellow"/"red" → Issues found
- Silver "Manual Review" → Needs deeper analysis
- Claim amount > $5000 → Extra scrutiny

### Rule 3: USE TIERED APPROACH

**🟢 CLEAN CLAIM (no red flags):**
1. assess_risk - Quick check
2. generate_insights - Basic insights
3. write_gold with AUTO_APPROVE
Done in 3-4 tool calls.

**🟡 SUSPICIOUS CLAIM (red flags present):**
1. check_fraud_indicators - FIRST
2. If fraud_score > 25%: velocity_check, duplicate_check, fraud_pattern_match
3. generate_insights with findings
4. write_gold with REVIEW/INVESTIGATE
Done in 5-8 tool calls.

### Rule 4: STOP CONDITIONS

MUST call write_gold when:
- Clean claim + fraud_score < 25% → AUTO_APPROVE
- Investigation done + no fraud → APPROVE  
- Investigation done + fraud found → INVESTIGATE/DENY
- 7+ tool calls made → FINISH NOW

### Rule 5: FINISH PROTOCOL

Write:
```
✅ DECISION: [AUTO_APPROVE/STANDARD_REVIEW/MANUAL_REVIEW/INVESTIGATION/DENY]
📊 FRAUD_SCORE: [0-100]%
📝 REASON: [One sentence]
```
Then call write_gold IMMEDIATELY.

## TOOLS BY CATEGORY

**Quick Assessment:**
- assess_risk, generate_insights, calculate_kpi_metrics

**Fraud Investigation (use when suspicious):**
- check_fraud_indicators, velocity_check, duplicate_check
- fraud_pattern_match, provider_customer_analysis

**REQUIRED:**
- write_gold - MUST CALL TO COMPLETE

## DECISION THRESHOLDS

| Fraud Score | Decision |
|-------------|----------|
| 0-24% | AUTO_APPROVE |
| 25-49% | STANDARD_REVIEW |
| 50-74% | MANUAL_REVIEW |
| 75-100% | INVESTIGATION |

## UI Card Display (REQUIRED)

Include at END:

```card_display
{
  "title": "Gold Layer",
  "subtitle": "AI Decision Agent",
  "primary_metric": {"label": "Fraud Risk", "value": "12%"},
  "amount": 850.00,
  "amount_label": "Approved Amount",
  "secondary_metrics": [
    {"label": "Confidence", "value": "92%"},
    {"label": "Risk Level", "value": "Low"}
  ],
  "decision": "Approved",
  "decision_color": "green",
  "summary": "One sentence summary"
}
```

ALWAYS call write_gold at the end."""


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

    def _check_if_suspicious(self, silver_data: dict) -> bool:
        """Check if claim has red flags from previous layers."""
        # Check Bronze flags
        bronze_ref = silver_data.get('bronze_reference', {})
        if bronze_ref.get('decision') == 'quarantine':
            return True
        
        anomaly_result = bronze_ref.get('anomaly_result', {})
        if isinstance(anomaly_result, dict) and anomaly_result.get('anomaly_score', 0) > 0.3:
            return True
        
        # Check Silver flags
        card_display = silver_data.get('card_display', {})
        if card_display.get('status_color') in ['yellow', 'red']:
            return True
        if card_display.get('status') in ['Manual Review', 'Review Required']:
            return True
        
        # Check claim amount
        claim_amount = bronze_ref.get('cleaned_data', {}).get('claim_amount', 0)
        if claim_amount and claim_amount > 5000:
            return True
        
        return False

    def _create_forced_completion(self, claim_id: str, silver_data: dict, error: str) -> dict:
        """Create a completion result when agent hits recursion limit."""
        expected_reimbursement = silver_data.get('expected_reimbursement', 0)
        
        return {
            "success": True,
            "claim_id": claim_id,
            "final_decision": "MANUAL_REVIEW",
            "fraud_score": 0.5,
            "risk_level": "medium",
            "approved_amount": expected_reimbursement,
            "confidence": 0.5,
            "insights": ["Agent analysis incomplete - manual review recommended"],
            "alerts": [{
                "type": "processing",
                "severity": "warning",
                "message": "Gold agent reached iteration limit. Claim requires manual review."
            }],
            "alerts_count": 1,
            "reasoning": f"Analysis incomplete. Defaulting to manual review. Error: {error}",
            "card_display": {
                "title": "Gold Layer",
                "subtitle": "AI Decision Agent",
                "primary_metric": {"label": "Fraud Score", "value": "50%"},
                "amount": expected_reimbursement,
                "amount_label": "Pending Review",
                "secondary_metrics": [
                    {"label": "Risk Level", "value": "Medium"},
                    {"label": "Status", "value": "Incomplete"}
                ],
                "decision": "Manual Review",
                "decision_color": "yellow",
                "summary": "Analysis incomplete - manual review required"
            },
            "forced_completion": True,
            "original_error": error
        }

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

            # Determine if this is a suspicious claim
            is_suspicious = self._check_if_suspicious(silver_data)
            path_hint = "⚠️ RED FLAGS DETECTED - Use SUSPICIOUS CLAIM PATH (more tools)" if is_suspicious else "✅ No red flags - Use CLEAN CLAIM PATH (fast, 3-4 tools)"
            
            # Get claim summary for input
            bronze_ref = silver_data.get('bronze_reference', {})
            cleaned_data = bronze_ref.get('cleaned_data', {})
            
            # Create input message with tiered guidance
            input_message = f"""Analyze this claim through Gold Layer.

## Previous Layer Results

**Bronze Summary:**
- Decision: {bronze_ref.get('decision', 'N/A')}
- Quality Score: {bronze_ref.get('quality_score', 'N/A')}

**Silver Summary:**
- Coverage: {silver_data.get('is_covered', 'N/A')}
- Expected Reimbursement: ${silver_data.get('expected_reimbursement', 0)}
- Status: {silver_data.get('card_display', {}).get('status', 'N/A')}
- Status Color: {silver_data.get('card_display', {}).get('status_color', 'N/A')}

## Claim Details
- Claim ID: {claim_id}
- Amount: ${cleaned_data.get('claim_amount', 'N/A')}
- Customer: {cleaned_data.get('customer_id', 'N/A')}
- Pet: {cleaned_data.get('pet_id', 'N/A')}
- Diagnosis: {cleaned_data.get('diagnosis', 'N/A')}

## Your Task
{path_hint}

Remember:
1. THINK OUT LOUD before each tool call
2. Call write_gold to finish
3. Max {settings.AGENT_RECURSION_LIMIT} iterations allowed"""

            # Publish step events
            await events.start_step("Risk Assessment")
            await events.reason(
                f"Starting {'thorough' if is_suspicious else 'quick'} analysis for claim {claim_id}",
                reasoning_type="analysis"
            )

            # Run the agent with configurable recursion limit
            try:
                result_state = await self.agent.ainvoke(
                    {"messages": [HumanMessage(content=input_message)]},
                    config={"recursion_limit": settings.AGENT_RECURSION_LIMIT},
                )
            except Exception as invoke_error:
                error_msg = str(invoke_error)
                if "recursion limit" in error_msg.lower():
                    logger.warning(f"Gold Agent hit recursion limit for {claim_id}, forcing completion")
                    return self._create_forced_completion(claim_id, silver_data, error_msg)
                raise

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
        # Defensive: ensure state is a dict
        if not isinstance(state, dict):
            state = {"messages": []}
        messages = state.get("messages", [])

        # Defensive: ensure silver_data is a dict
        if not isinstance(silver_data, dict):
            silver_data = {}

        # Get expected reimbursement from Silver layer for approved amount
        expected_reimbursement = silver_data.get("expected_reimbursement", 0)

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
            "approved_amount": expected_reimbursement,  # Use Silver's amount by default
            "confidence": 0.85,
            "reasoning": "",
            "card_display": None,  # AI-generated card display
        }

        # Extract from AI messages
        for msg in messages:
            if isinstance(msg, AIMessage):
                if not hasattr(msg, "tool_calls") or not msg.tool_calls:
                    content = msg.content.lower()
                    original_content = msg.content
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

                    # Extract card_display JSON block
                    card_display = self._extract_card_display(original_content)
                    if card_display:
                        result["card_display"] = card_display
                        # Also extract approved_amount from card_display if present
                        if card_display.get("amount"):
                            result["approved_amount"] = float(card_display["amount"])

        # Generate fallback card_display if AI didn't provide one
        if not result["card_display"]:
            result["card_display"] = self._generate_fallback_card(result, expected_reimbursement)

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

    def _generate_fallback_card(self, result: dict, expected_reimbursement: float) -> dict:
        """Generate fallback card display if AI didn't provide one."""
        decision = result.get("final_decision", "auto_approve")
        fraud_score = result.get("fraud_score", 0.15)
        confidence = result.get("confidence", 0.85)
        risk_level = result.get("risk_level", "low")

        decision_map = {
            "auto_approve": ("Approved", "green"),
            "standard_review": ("Standard Review", "yellow"),
            "manual_review": ("Manual Review", "yellow"),
            "investigation": ("Investigation Required", "orange"),
            "deny": ("Denied", "red"),
        }
        decision_text, color = decision_map.get(decision, ("Processed", "blue"))

        # Set amount to 0 if denied or under investigation
        amount = expected_reimbursement if decision in ["auto_approve", "standard_review"] else 0

        return {
            "title": "Gold Layer",
            "subtitle": "AI Decision & Fraud Detection Agent",
            "primary_metric": {"label": "Fraud Risk", "value": f"{int(fraud_score * 100)}%"},
            "amount": amount,
            "amount_label": "Approved Amount",
            "secondary_metrics": [
                {"label": "Confidence", "value": f"{int(confidence * 100)}%"},
                {"label": "Risk Level", "value": risk_level.capitalize()}
            ],
            "decision": decision_text,
            "decision_color": color,
            "summary": result.get("reasoning", "Decision analysis completed.")[:100]
        }


# Create singleton instance
gold_agent = GoldAgent()
