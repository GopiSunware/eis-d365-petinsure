"""OpenAI client wrapper - supports both Azure OpenAI and regular OpenAI API."""
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI, AsyncAzureOpenAI

from ..config import get_settings
from ..ai_config import get_ai_config


class OpenAIClient:
    """Wrapper for OpenAI API (supports both Azure and regular OpenAI)."""

    def __init__(self):
        self.settings = get_settings()

        # Check which OpenAI service to use
        if self.settings.openai_api_key:
            # Use regular OpenAI API (api.openai.com)
            self.client = AsyncOpenAI(
                api_key=self.settings.openai_api_key,
            )
            self.is_azure = False
        elif self.settings.azure_openai_api_key and self.settings.azure_openai_endpoint:
            # Use Azure OpenAI
            self.client = AsyncAzureOpenAI(
                api_key=self.settings.azure_openai_api_key,
                api_version=self.settings.azure_openai_api_version,
                azure_endpoint=self.settings.azure_openai_endpoint,
            )
            self.is_azure = True
        else:
            # No OpenAI configured - will fail on use
            self.client = None
            self.is_azure = False

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> str:
        """Get chat completion from OpenAI."""
        if self.client is None:
            raise RuntimeError("OpenAI not configured. Set OPENAI_API_KEY or AZURE_OPENAI_* environment variables.")

        # Get runtime config for defaults
        ai_config = get_ai_config()

        # Use provided values or fall back to runtime config
        if model:
            actual_model = model
        elif ai_config.provider == "openai":
            actual_model = ai_config.model_id
        elif self.is_azure:
            actual_model = self.settings.azure_openai_deployment_name
        else:
            actual_model = "gpt-4o"  # Default for regular OpenAI

        actual_temp = temperature if temperature is not None else ai_config.temperature
        actual_tokens = max_tokens or ai_config.max_tokens

        kwargs: Dict[str, Any] = {
            "model": actual_model,
            "messages": messages,
            "temperature": actual_temp,
            "max_tokens": actual_tokens,
        }

        if response_format:
            kwargs["response_format"] = response_format

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def structured_extraction(
        self,
        text: str,
        schema: Dict[str, Any],
        system_prompt: str = "Extract structured data from the provided text.",
    ) -> Dict[str, Any]:
        """Extract structured data using JSON mode."""
        import json

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Text to analyze:\n\n{text}\n\nExtract data according to this schema:\n{json.dumps(schema, indent=2)}"},
        ]

        response = await self.chat_completion(
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        return json.loads(response)


# Keep old name for backwards compatibility
AzureOpenAIClient = OpenAIClient

# Singleton
_client: Optional[OpenAIClient] = None


def get_openai_client() -> OpenAIClient:
    """Get or create OpenAI client singleton."""
    global _client
    if _client is None:
        _client = OpenAIClient()
    return _client
