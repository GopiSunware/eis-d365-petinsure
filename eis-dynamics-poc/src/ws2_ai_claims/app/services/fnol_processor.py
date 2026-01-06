"""FNOL Processor - AI-powered claim intake and triage."""
import logging
from typing import Any, Dict

from eis_common.azure import get_claude_client, get_openai_client
from eis_common.config import get_settings

from ..prompts.extraction import EXTRACTION_PROMPT, TRIAGE_PROMPT

logger = logging.getLogger(__name__)
settings = get_settings()


class FNOLProcessor:
    """Processes First Notice of Loss submissions with AI."""

    def __init__(self):
        self.use_claude = bool(settings.anthropic_api_key)
        self.use_openai = bool(settings.azure_openai_api_key)

    async def extract_claim_data(self, description: str) -> Dict[str, Any]:
        """
        Extract structured data from claim description using AI.

        Returns:
            dict with incident_type, severity, damage_description, etc.
        """
        logger.info("Extracting claim data with AI...")

        try:
            if self.use_claude:
                client = get_claude_client()
                result = await client.structured_extraction(
                    text=description,
                    schema={
                        "incident_type": "string",
                        "incident_date": "string or null",
                        "incident_location": "string or null",
                        "damage_description": "string",
                        "estimated_amount": "number or null",
                        "parties_involved": "array",
                        "severity": "minor | moderate | severe",
                        "confidence_score": "number 0-1",
                    },
                    system_prompt=EXTRACTION_PROMPT,
                )
            elif self.use_openai:
                client = get_openai_client()
                result = await client.structured_extraction(
                    text=description,
                    schema={
                        "incident_type": "string",
                        "severity": "string",
                    },
                    system_prompt=EXTRACTION_PROMPT,
                )
            else:
                # Fallback: simple rule-based extraction
                result = self._fallback_extraction(description)

            logger.info(f"Extracted: type={result.get('incident_type')}, severity={result.get('severity')}")
            return result

        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            return self._fallback_extraction(description)

    def _fallback_extraction(self, description: str) -> Dict[str, Any]:
        """Fallback rule-based extraction when AI is unavailable."""
        description_lower = description.lower()

        # Determine incident type
        if any(word in description_lower for word in ["hit", "crash", "collision", "accident"]):
            incident_type = "collision"
        elif any(word in description_lower for word in ["stolen", "theft", "burglar"]):
            incident_type = "theft"
        elif any(word in description_lower for word in ["hail", "storm", "flood", "weather"]):
            incident_type = "weather"
        elif any(word in description_lower for word in ["vandal", "keyed", "damage"]):
            incident_type = "vandalism"
        else:
            incident_type = "other"

        # Determine severity
        if any(word in description_lower for word in ["total", "severe", "major", "hospital", "injury"]):
            severity = "severe"
        elif any(word in description_lower for word in ["moderate", "significant", "several"]):
            severity = "moderate"
        else:
            severity = "minor"

        return {
            "incident_type": incident_type,
            "incident_date": None,
            "incident_location": None,
            "damage_description": description[:500],
            "estimated_amount": None,
            "parties_involved": [],
            "severity": severity,
            "confidence_score": 0.5,
        }

    async def triage_claim(
        self,
        extraction: Dict[str, Any],
        fraud_score: float,
    ) -> Dict[str, Any]:
        """
        Determine claim triage based on extraction and fraud analysis.

        Returns:
            dict with priority, recommended_handler, estimated_reserve, etc.
        """
        severity = extraction.get("severity", "moderate")
        incident_type = extraction.get("incident_type", "other")

        # Priority: 1 (highest) to 5 (lowest)
        priority_map = {
            "severe": 1,
            "moderate": 3,
            "minor": 5,
        }
        base_priority = priority_map.get(severity, 3)

        # Adjust for fraud risk
        if fraud_score > 0.7:
            base_priority = 1  # High fraud = high priority for investigation
        elif fraud_score > 0.4:
            base_priority = min(base_priority, 2)

        # Handler assignment
        if fraud_score > 0.5:
            handler = "Special Investigations Unit"
        elif severity == "severe":
            handler = "Senior Claims Adjuster"
        elif severity == "moderate":
            handler = "Claims Adjuster"
        else:
            handler = "Claims Associate"

        # Estimated reserve
        reserve_map = {
            "collision": {"severe": 25000, "moderate": 8000, "minor": 2000},
            "theft": {"severe": 20000, "moderate": 10000, "minor": 3000},
            "weather": {"severe": 15000, "moderate": 5000, "minor": 1500},
            "vandalism": {"severe": 5000, "moderate": 2000, "minor": 500},
            "other": {"severe": 10000, "moderate": 4000, "minor": 1000},
        }
        type_reserves = reserve_map.get(incident_type, reserve_map["other"])
        estimated_reserve = type_reserves.get(severity, 5000)

        # Auto-approve eligibility
        auto_approve = (
            severity == "minor"
            and fraud_score < 0.2
            and estimated_reserve < 1000
        )

        # Next steps
        next_steps = []
        if fraud_score > 0.5:
            next_steps.append("Route to SIU for investigation")
        if severity in ["severe", "moderate"]:
            next_steps.append("Schedule adjuster inspection")
        if extraction.get("parties_involved"):
            next_steps.append("Contact third parties")
        next_steps.append("Request supporting documentation")
        if auto_approve:
            next_steps = ["Eligible for straight-through processing"]

        recommendation = f"Assign to {handler}. " + " ".join(next_steps[:2])

        return {
            "priority": base_priority,
            "recommended_handler": handler,
            "estimated_reserve": estimated_reserve,
            "next_steps": next_steps,
            "auto_approve_eligible": auto_approve,
            "recommendation": recommendation,
        }
