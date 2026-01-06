"""Fraud Detection Service - AI-powered fraud indicator analysis."""
import logging
from typing import Any, Dict, List

from eis_common.azure import get_claude_client, get_openai_client
from eis_common.config import get_settings

from ..prompts.extraction import FRAUD_DETECTION_PROMPT

logger = logging.getLogger(__name__)
settings = get_settings()


class FraudDetector:
    """Detects potential fraud indicators in claims using AI."""

    def __init__(self):
        self.use_claude = bool(settings.anthropic_api_key)
        self.use_openai = bool(settings.azure_openai_api_key)

    async def analyze(
        self,
        description: str,
        extraction: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analyze claim for fraud indicators.

        Returns:
            dict with fraud_score, risk_level, indicators, recommendation
        """
        logger.info("Running fraud analysis...")

        try:
            if self.use_claude:
                result = await self._analyze_with_claude(description, extraction)
            elif self.use_openai:
                result = await self._analyze_with_openai(description, extraction)
            else:
                result = self._fallback_analysis(description, extraction)

            logger.info(f"Fraud analysis: score={result['fraud_score']}, risk={result['risk_level']}")
            return result

        except Exception as e:
            logger.error(f"Fraud analysis failed: {e}")
            return self._fallback_analysis(description, extraction)

    async def _analyze_with_claude(
        self,
        description: str,
        extraction: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze using Claude."""
        client = get_claude_client()

        messages = [
            {
                "role": "user",
                "content": f"""Analyze this insurance claim for fraud indicators.

Claim Description:
{description}

Extracted Data:
- Incident Type: {extraction.get('incident_type')}
- Severity: {extraction.get('severity')}
- Estimated Amount: {extraction.get('estimated_amount')}

Return JSON with:
- fraud_score: number 0-1 (0=no fraud risk, 1=definite fraud)
- risk_level: "low" | "medium" | "high"
- indicators: array of {{indicator, confidence, description}}
- recommendation: string (suggested action)""",
            }
        ]

        result = await client.chat_completion(
            messages=messages,
            system=FRAUD_DETECTION_PROMPT,
            temperature=0.1,
        )

        # Parse JSON response
        import json
        result = result.strip()
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]

        return json.loads(result.strip())

    async def _analyze_with_openai(
        self,
        description: str,
        extraction: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze using Azure OpenAI."""
        client = get_openai_client()

        messages = [
            {"role": "system", "content": FRAUD_DETECTION_PROMPT},
            {
                "role": "user",
                "content": f"Analyze for fraud: {description}\nSeverity: {extraction.get('severity')}\nType: {extraction.get('incident_type')}",
            },
        ]

        result = await client.chat_completion(
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        import json
        return json.loads(result)

    def _fallback_analysis(
        self,
        description: str,
        extraction: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Fallback rule-based fraud detection."""
        indicators: List[Dict[str, Any]] = []
        fraud_score = 0.0
        description_lower = description.lower()

        # Check for common fraud indicators
        if any(word in description_lower for word in ["cash", "cash only", "no receipt"]):
            indicators.append({
                "indicator": "Cash payment preference",
                "confidence": 0.6,
                "description": "Claimant prefers cash payment, potential red flag",
            })
            fraud_score += 0.15

        if any(word in description_lower for word in ["just happened", "yesterday", "last night"]):
            # Recent claims can be legitimate, low weight
            pass

        if "police" not in description_lower and extraction.get("severity") == "severe":
            indicators.append({
                "indicator": "No police report for severe incident",
                "confidence": 0.5,
                "description": "Severe incident reported without police involvement",
            })
            fraud_score += 0.1

        if any(word in description_lower for word in ["total loss", "totaled"]):
            indicators.append({
                "indicator": "Total loss claim",
                "confidence": 0.3,
                "description": "Total loss claims require additional verification",
            })
            fraud_score += 0.05

        # Adjust for extraction confidence
        if extraction.get("confidence_score", 1.0) < 0.5:
            indicators.append({
                "indicator": "Low extraction confidence",
                "confidence": 0.4,
                "description": "Claim description may be vague or inconsistent",
            })
            fraud_score += 0.1

        # Cap fraud score
        fraud_score = min(fraud_score, 0.95)

        # Determine risk level
        if fraud_score > 0.6:
            risk_level = "high"
        elif fraud_score > 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Recommendation
        if risk_level == "high":
            recommendation = "Route to Special Investigations Unit for detailed review"
        elif risk_level == "medium":
            recommendation = "Flag for supervisor review before processing"
        else:
            recommendation = "Proceed with standard claims processing"

        return {
            "fraud_score": round(fraud_score, 2),
            "risk_level": risk_level,
            "indicators": indicators,
            "recommendation": recommendation,
        }
