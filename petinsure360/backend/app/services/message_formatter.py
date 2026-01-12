"""
Message Formatter Service
Calls the existing Chat API to format technical messages for customer display.
Uses the same AI providers (OpenAI/Anthropic) as the chat sidebar.
"""

import os
import logging
from typing import Optional, Dict, Any

import httpx

logger = logging.getLogger(__name__)

# Claims Data API URL (has the chat endpoint)
CLAIMS_API_URL = os.getenv("CLAIMS_API_URL", "http://localhost:8000")


async def format_user_message(
    status: str,
    technical_message: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format a technical message into a customer-friendly message using AI.

    Args:
        status: Processing status ("completed", "failed", "queued")
        technical_message: Raw technical/error message from processing
        context: Optional context (pet_name, filenames, etc.)

    Returns:
        Customer-friendly message string
    """
    if not technical_message:
        return get_fallback_message(status, context)

    context = context or {}
    pet_name = context.get("pet_name", "your pet")
    filenames = context.get("filenames", [])

    # Build prompt for AI
    prompt = f"""You are a friendly customer service assistant for PetInsure360 pet insurance.

Format this document processing result into a brief, friendly message for the customer.

**Status:** {status}
**Technical Message:** {technical_message}
**Pet Name:** {pet_name}
**Documents:** {', '.join(filenames) if filenames else 'Document'}

**Rules:**
- Be warm, friendly, and reassuring
- Keep it to 1-2 sentences maximum
- Never show technical details, batch IDs, error codes, or file hashes
- For duplicates: Simply explain they already submitted this document
- For success: Confirm the document was processed and mention next steps
- For queued: Explain documents are saved and will be processed soon
- Use the pet's name if available
- Don't apologize excessively

Return ONLY the customer-friendly message, nothing else."""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{CLAIMS_API_URL}/api/chat",
                json={
                    "provider": None,  # Use default provider
                    "messages": [{"role": "user", "content": prompt}]
                }
            )

            if response.status_code == 200:
                result = response.json()
                ai_message = result.get("response", {}).get("content", "")

                if ai_message:
                    logger.info(f"AI formatted message for status={status}")
                    return ai_message.strip()

            logger.warning(f"Chat API returned status {response.status_code}")

    except httpx.ConnectError:
        logger.warning("Chat API unavailable, using fallback message")
    except Exception as e:
        logger.error(f"Error calling chat API for message formatting: {e}")

    # Fallback to template-based messages
    return get_fallback_message(status, context)


def get_fallback_message(status: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Get a fallback message when AI is unavailable.
    Uses template-based messages based on status and error type.
    """
    context = context or {}
    pet_name = context.get("pet_name")
    technical_message = context.get("technical_message", "")

    # Check for specific error types
    is_duplicate = "DUPLICATE" in technical_message.upper() if technical_message else False

    if status == "completed":
        if pet_name:
            return f"Great news! Your documents for {pet_name} have been processed successfully. We'll review your claim shortly."
        return "Your documents have been processed successfully. We'll review your claim shortly."

    elif status == "failed":
        if is_duplicate:
            if pet_name:
                return f"It looks like you've already submitted this document for {pet_name}. No need to upload it again - we have it on file!"
            return "It looks like you've already submitted this document. No need to upload it again - we have it on file!"
        else:
            # Generic failure - show as "in review" to not alarm customer
            return "Your documents are being reviewed by our team. We'll notify you once processing is complete."

    elif status == "queued":
        if pet_name:
            return f"Your documents for {pet_name} have been saved and will be processed shortly. We'll notify you when complete."
        return "Your documents have been saved and will be processed shortly. We'll notify you when complete."

    else:
        return "Your documents are being processed. We'll notify you once complete."


async def format_success_message(
    claim_number: str,
    ai_decision: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """Format a success message when claim is created."""
    context = context or {}
    pet_name = context.get("pet_name", "your pet")

    technical_message = f"Claim {claim_number} created successfully. AI Decision: {ai_decision}"

    return await format_user_message(
        status="completed",
        technical_message=technical_message,
        context={**context, "technical_message": technical_message}
    )


async def format_error_message(
    error_message: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """Format an error message for customer display."""
    context = context or {}

    return await format_user_message(
        status="failed",
        technical_message=error_message,
        context={**context, "technical_message": error_message}
    )
