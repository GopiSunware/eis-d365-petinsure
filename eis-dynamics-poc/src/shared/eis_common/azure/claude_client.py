"""Anthropic Claude client wrapper."""
from typing import Any, Dict, List, Optional

import anthropic

from ..config import get_settings
from ..ai_config import get_ai_config


class ClaudeClient:
    """Wrapper for Anthropic Claude API."""

    def __init__(self):
        self.settings = get_settings()
        self.client = anthropic.AsyncAnthropic(
            api_key=self.settings.anthropic_api_key,
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> str:
        """Get chat completion from Claude."""
        # Get runtime config for defaults
        ai_config = get_ai_config()

        # Use provided values or fall back to runtime config
        actual_model = model or ai_config.model_id
        actual_temp = temperature if temperature is not None else ai_config.temperature
        actual_tokens = max_tokens or ai_config.max_tokens

        response = await self.client.messages.create(
            model=actual_model,
            max_tokens=actual_tokens,
            temperature=actual_temp,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    async def structured_extraction(
        self,
        text: str,
        schema: Dict[str, Any],
        system_prompt: str = "Extract structured data from the provided text. Respond with valid JSON only.",
    ) -> Dict[str, Any]:
        """Extract structured data from text."""
        import json

        messages = [
            {
                "role": "user",
                "content": f"""Analyze this text and extract structured data according to the schema.

Text:
{text}

Schema:
{json.dumps(schema, indent=2)}

Respond with valid JSON only, no additional text.""",
            }
        ]

        response = await self.chat_completion(
            messages=messages,
            system=system_prompt,
            temperature=0.1,
        )

        # Clean response and parse JSON
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        return json.loads(response.strip())

    async def analyze_claim(
        self,
        description: str,
        policy_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze a claim description for structured extraction and fraud detection."""
        system = """You are an insurance claims analyst AI. Analyze claim descriptions to:
1. Extract structured incident details
2. Assess severity (minor, moderate, severe)
3. Identify potential fraud indicators
4. Recommend next steps

Be thorough but concise. Respond in JSON format."""

        context = f"\nPolicy context: {policy_context}" if policy_context else ""

        messages = [
            {
                "role": "user",
                "content": f"""Analyze this insurance claim:

Claim Description:
{description}
{context}

Extract and return JSON with:
- incident_type: string (collision, theft, vandalism, weather, injury, other)
- incident_date: string or null (if mentioned)
- incident_location: string or null
- damage_description: string
- estimated_amount: number or null
- parties_involved: array of objects with name and role
- severity: "minor" | "moderate" | "severe"
- fraud_indicators: array of objects with indicator, confidence (0-1), description
- fraud_score: number 0-1 (overall fraud risk)
- recommended_action: string
- confidence_score: number 0-1 (confidence in extraction)""",
            }
        ]

        return await self.structured_extraction(
            text=description,
            schema={
                "incident_type": "string",
                "severity": "string",
                "fraud_score": "number",
            },
            system_prompt=system,
        )


# Singleton
_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get or create Claude client singleton."""
    global _client
    if _client is None:
        _client = ClaudeClient()
    return _client
