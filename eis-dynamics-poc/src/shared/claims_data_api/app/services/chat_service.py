"""
Chat Service for AI-powered assistant
Provides chat endpoints with OpenAI and Anthropic support with conversation persistence
"""

import os
import base64
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Session storage directory
BASE_DIR = Path(__file__).parent.parent.parent
SESSION_DIR = BASE_DIR / "data" / "session_user"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

# Load site context from SITE_CONTEXT.md if available
def load_site_context() -> str:
    """Load site context from markdown file"""
    # Try multiple paths to find the context file
    possible_paths = [
        Path(__file__).parent.parent.parent.parent.parent.parent.parent / "petinsure360" / "SITE_CONTEXT.md",
        Path("/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/SITE_CONTEXT.md"),
        Path("SITE_CONTEXT.md"),
    ]

    for path in possible_paths:
        if path.exists():
            try:
                content = path.read_text(encoding='utf-8')
                logger.info(f"Loaded site context from: {path}")
                return content
            except Exception as e:
                logger.warning(f"Failed to read {path}: {e}")

    logger.warning("SITE_CONTEXT.md not found, using default prompt")
    return ""

# Load context once at startup
SITE_CONTEXT = load_site_context()

# System prompt for claims processing assistant
SYSTEM_PROMPT = SITE_CONTEXT if SITE_CONTEXT else """You are a helpful claims processing assistant for a Pet Insurance Portal (EIS-D365).

## Your Role
- Help users understand claim status, processing pipeline, and decisions
- Explain the Bronze/Silver/Gold agent pipeline flow
- Analyze fraud indicators and validation results
- Answer questions about policy coverage and claim amounts
- Be concise and focus on actionable insights
- Use the page context to understand what the user is looking at

## Response Style
- Be conversational but informative
- When explaining decisions, cite specific data points
- Relate back to practical implications (claim approved/denied, coverage limits)
- Use specific numbers from the data when available

## Claims Processing Pipeline
- **Bronze Agent**: Initial validation, data quality checks, format verification
- **Silver Agent**: Policy enrichment, coverage verification, provider validation
- **Gold Agent**: Final decision, fraud detection, risk assessment

## Important Guidelines
- Currency is in USD
- Fraud score 0-100: <30 Low, 30-60 Medium, >60 High risk
- Always explain the reasoning behind decisions
- If unsure, recommend manual review"""


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    provider: Optional[str] = None
    messages: List[ChatMessage]
    screenshot: Optional[str] = None
    appContext: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = "guest"  # User identifier for session persistence
    session_id: Optional[str] = "default"  # Session identifier


# Helper functions for chat persistence
def get_user_session_dir(user_id: str) -> Path:
    """Get or create user session directory"""
    user_dir = SESSION_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_session_file(user_id: str, session_id: str) -> Path:
    """Get session file path"""
    user_dir = get_user_session_dir(user_id)
    return user_dir / f"{session_id}.json"


def save_chat_history(user_id: str, session_id: str, messages: List[Dict], metadata: Optional[Dict] = None):
    """Save chat conversation to user session file"""
    try:
        session_file = get_session_file(user_id, session_id)

        history = {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": messages,
            "metadata": metadata or {}
        }

        # If file exists, preserve created_at
        if session_file.exists():
            try:
                existing = json.loads(session_file.read_text())
                history["created_at"] = existing.get("created_at", history["created_at"])
            except Exception as e:
                logger.warning(f"Failed to read existing session: {e}")

        session_file.write_text(json.dumps(history, indent=2))
        logger.info(f"Saved chat history: {user_id}/{session_id} ({len(messages)} messages)")

    except Exception as e:
        logger.error(f"Failed to save chat history: {e}")


def load_chat_history(user_id: str, session_id: str) -> Optional[Dict]:
    """Load chat conversation from user session file"""
    try:
        session_file = get_session_file(user_id, session_id)

        if not session_file.exists():
            return None

        history = json.loads(session_file.read_text())
        logger.info(f"Loaded chat history: {user_id}/{session_id} ({len(history.get('messages', []))} messages)")
        return history

    except Exception as e:
        logger.error(f"Failed to load chat history: {e}")
        return None


def list_user_sessions(user_id: str) -> List[Dict]:
    """List all sessions for a user"""
    try:
        user_dir = get_user_session_dir(user_id)
        sessions = []

        for session_file in user_dir.glob("*.json"):
            try:
                history = json.loads(session_file.read_text())
                sessions.append({
                    "session_id": history.get("session_id", session_file.stem),
                    "created_at": history.get("created_at"),
                    "updated_at": history.get("updated_at"),
                    "message_count": len(history.get("messages", []))
                })
            except Exception as e:
                logger.warning(f"Failed to read session {session_file}: {e}")

        # Sort by updated_at (most recent first)
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions

    except Exception as e:
        logger.error(f"Failed to list user sessions: {e}")
        return []


class AIProvider:
    """Base class for AI providers"""

    def __init__(self):
        self.name = "base"
        self.enabled = False
        self.model = ""

    def is_enabled(self) -> bool:
        return self.enabled

    def get_name(self) -> str:
        return self.name

    def get_model(self) -> str:
        return self.model

    async def chat(self, messages: List[Dict], image_base64: Optional[str], app_context: Optional[Dict]) -> Dict:
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    """OpenAI GPT-4o provider with vision support"""

    def __init__(self):
        super().__init__()
        self.name = "OpenAI"
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        # Enable by default if API key is present (USE_OPENAI defaults to "true")
        use_openai = os.getenv("USE_OPENAI", "true").lower()
        self.enabled = bool(self.api_key) and use_openai != "false"
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = None

        if self.enabled:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info(f"OpenAI provider initialized: {self.model}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
                self.enabled = False

    async def chat(self, messages: List[Dict], image_base64: Optional[str], app_context: Optional[Dict]) -> Dict:
        if not self.client:
            raise Exception("OpenAI client not initialized")

        # Build system content
        system_content = SYSTEM_PROMPT
        if app_context:
            system_content += f"\n\n## Current App State\n{json.dumps(app_context, indent=2)}"

        # Build messages for API
        api_messages = [{"role": "system", "content": system_content}]

        for i, msg in enumerate(messages):
            if msg["role"] == "user" and image_base64 and i == len(messages) - 1:
                # Include image with the last user message
                api_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_base64, "detail": "high"}
                        },
                        {"type": "text", "text": msg["content"]}
                    ]
                })
            else:
                api_messages.append({"role": msg["role"], "content": msg["content"]})

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=api_messages,
            max_tokens=1500,
            temperature=0.7
        )

        content = response.choices[0].message.content or ""
        usage = response.usage

        # Calculate cost (GPT-4o-mini pricing)
        input_cost = (usage.prompt_tokens / 1000) * 0.00015
        output_cost = (usage.completion_tokens / 1000) * 0.0006
        estimated_cost = round(input_cost + output_cost, 4)

        return {
            "content": content,
            "provider": "openai",
            "model": response.model,
            "usage": {
                "promptTokens": usage.prompt_tokens,
                "completionTokens": usage.completion_tokens,
                "totalTokens": usage.total_tokens
            },
            "estimatedCost": estimated_cost
        }


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider with vision support"""

    def __init__(self):
        super().__init__()
        self.name = "Anthropic"
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        # Enable by default if API key is present (USE_ANTHROPIC defaults to "true")
        use_anthropic = os.getenv("USE_ANTHROPIC", "true").lower()
        self.enabled = bool(self.api_key) and use_anthropic != "false"
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        self.client = None

        if self.enabled:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
                logger.info(f"Anthropic provider initialized: {self.model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic: {e}")
                self.enabled = False

    async def chat(self, messages: List[Dict], image_base64: Optional[str], app_context: Optional[Dict]) -> Dict:
        if not self.client:
            raise Exception("Anthropic client not initialized")

        # Build system content
        system_content = SYSTEM_PROMPT
        if app_context:
            system_content += f"\n\n## Current App State\n{json.dumps(app_context, indent=2)}"

        # Build messages for API
        api_messages = []

        for i, msg in enumerate(messages):
            if msg["role"] == "user" and image_base64 and i == len(messages) - 1:
                # Parse the data URL to get media type and base64 data
                if image_base64.startswith("data:"):
                    parts = image_base64.split(",", 1)
                    media_type = parts[0].split(":")[1].split(";")[0]
                    base64_data = parts[1]
                else:
                    media_type = "image/jpeg"
                    base64_data = image_base64

                api_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_data
                            }
                        },
                        {"type": "text", "text": msg["content"]}
                    ]
                })
            else:
                api_messages.append({"role": msg["role"], "content": msg["content"]})

        # Call Anthropic API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            system=system_content,
            messages=api_messages
        )

        # Extract text content
        content = ""
        for block in response.content:
            if block.type == "text":
                content = block.text
                break

        usage = response.usage

        # Calculate cost (Claude Sonnet pricing)
        input_cost = (usage.input_tokens / 1000) * 0.003
        output_cost = (usage.output_tokens / 1000) * 0.015
        estimated_cost = round(input_cost + output_cost, 4)

        return {
            "content": content,
            "provider": "anthropic",
            "model": response.model,
            "usage": {
                "promptTokens": usage.input_tokens,
                "completionTokens": usage.output_tokens,
                "totalTokens": usage.input_tokens + usage.output_tokens
            },
            "estimatedCost": estimated_cost
        }


# Initialize providers
openai_provider = OpenAIProvider()
anthropic_provider = AnthropicProvider()

providers = {
    "openai": openai_provider,
    "anthropic": anthropic_provider
}


def get_enabled_providers() -> List[str]:
    """Get list of enabled provider names"""
    return [name for name, p in providers.items() if p.is_enabled()]


def get_default_provider() -> Optional[str]:
    """Get the default provider (first enabled one)"""
    enabled = get_enabled_providers()
    return enabled[0] if enabled else None


@router.get("/providers")
async def get_chat_providers():
    """Get available AI chat providers"""
    status = {}
    for name, provider in providers.items():
        status[name] = {
            "name": provider.get_name(),
            "enabled": provider.is_enabled(),
            "model": provider.get_model(),
            "description": "GPT-4o with vision capabilities" if name == "openai" else "Claude Sonnet with vision capabilities"
        }

    return {
        "providers": status,
        "enabled": get_enabled_providers(),
        "default": get_default_provider()
    }


@router.get("/status")
async def get_chat_status():
    """Simple status check for chat service"""
    enabled = get_enabled_providers()
    return {
        "available": len(enabled) > 0,
        "providers": enabled
    }


@router.post("")
async def send_chat_message(request: ChatRequest):
    """Send a chat message to the AI provider"""

    # Validate messages
    if not request.messages:
        raise HTTPException(status_code=400, detail="Missing messages array")

    for msg in request.messages:
        if msg.role not in ["user", "assistant"]:
            raise HTTPException(status_code=400, detail="Message role must be 'user' or 'assistant'")

    # Determine provider
    selected_provider = request.provider
    if not selected_provider:
        selected_provider = get_default_provider()
        if not selected_provider:
            raise HTTPException(
                status_code=503,
                detail="No AI providers available. Configure API keys in .env"
            )

    # Check if provider is enabled
    if selected_provider not in providers or not providers[selected_provider].is_enabled():
        raise HTTPException(
            status_code=400,
            detail=f"AI provider '{selected_provider}' is not enabled"
        )

    try:
        # Convert messages to dict format
        messages_dict = [{"role": m.role, "content": m.content} for m in request.messages]

        # Send to AI provider
        result = await providers[selected_provider].chat(
            messages_dict,
            request.screenshot,
            request.appContext
        )

        # Save conversation history (including the new assistant response)
        updated_messages = messages_dict + [{
            "role": "assistant",
            "content": result["content"]
        }]

        save_chat_history(
            user_id=request.user_id or "guest",
            session_id=request.session_id or "default",
            messages=updated_messages,
            metadata={
                "provider": result["provider"],
                "model": result["model"],
                "last_response_at": datetime.now().isoformat()
            }
        )

        return {
            "success": True,
            "response": {
                "content": result["content"],
                "provider": result["provider"],
                "model": result["model"]
            },
            "usage": result.get("usage"),
            "estimatedCost": result.get("estimatedCost"),
            "generated_at": datetime.now().isoformat(),
            "session_saved": True
        }

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chat response: {str(e)}"
        )


@router.get("/history")
async def get_chat_history(
    user_id: str = Query("guest", description="User identifier"),
    session_id: str = Query("default", description="Session identifier")
):
    """Get chat conversation history for a user session"""
    history = load_chat_history(user_id, session_id)

    if not history:
        return {
            "exists": False,
            "user_id": user_id,
            "session_id": session_id,
            "messages": []
        }

    return {
        "exists": True,
        "user_id": history.get("user_id"),
        "session_id": history.get("session_id"),
        "created_at": history.get("created_at"),
        "updated_at": history.get("updated_at"),
        "messages": history.get("messages", []),
        "metadata": history.get("metadata", {}),
        "message_count": len(history.get("messages", []))
    }


@router.get("/sessions")
async def get_user_sessions(
    user_id: str = Query("guest", description="User identifier")
):
    """List all chat sessions for a user"""
    sessions = list_user_sessions(user_id)

    return {
        "user_id": user_id,
        "total_sessions": len(sessions),
        "sessions": sessions
    }


@router.delete("/history")
async def delete_chat_history(
    user_id: str = Query("guest", description="User identifier"),
    session_id: str = Query("default", description="Session identifier")
):
    """Delete a chat session"""
    try:
        session_file = get_session_file(user_id, session_id)

        if not session_file.exists():
            raise HTTPException(status_code=404, detail="Session not found")

        session_file.unlink()
        logger.info(f"Deleted chat history: {user_id}/{session_id}")

        return {
            "success": True,
            "message": f"Session {session_id} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )


# Log provider status on import
def log_provider_status():
    """Log provider status for debugging"""
    logger.info("=" * 60)
    logger.info("AI CHAT PROVIDERS STATUS")
    logger.info("=" * 60)
    for name, provider in providers.items():
        icon = "✓" if provider.is_enabled() else "✗"
        logger.info(f"  {icon} {provider.get_name()} ({provider.get_model()}): {'ENABLED' if provider.is_enabled() else 'DISABLED'}")

    default = get_default_provider()
    if default:
        logger.info(f"\n  Default provider: {default}")
    else:
        logger.info("\n  ⚠️  No AI providers enabled. Set API keys in .env")
    logger.info("=" * 60)


# Don't log on import as logger may not be configured yet
