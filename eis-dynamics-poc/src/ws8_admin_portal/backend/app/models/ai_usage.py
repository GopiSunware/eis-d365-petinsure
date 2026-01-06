"""AI API usage and token tracking models."""

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AIProvider(str, Enum):
    """AI provider."""
    AZURE_OPENAI = "azure_openai"
    AWS_BEDROCK = "aws_bedrock"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class AIModel(str, Enum):
    """AI model identifiers."""
    # Azure OpenAI
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_35_TURBO = "gpt-35-turbo"
    TEXT_EMBEDDING_ADA = "text-embedding-ada-002"
    TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"
    TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"

    # AWS Bedrock
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"
    CLAUDE_35_SONNET = "claude-3.5-sonnet"
    TITAN_TEXT = "titan-text"
    TITAN_EMBED = "titan-embed"


# Token pricing per 1K tokens (as of 2024)
TOKEN_PRICING = {
    # Azure OpenAI / OpenAI (per 1K tokens)
    AIModel.GPT_4: {"input": 0.03, "output": 0.06},
    AIModel.GPT_4_TURBO: {"input": 0.01, "output": 0.03},
    AIModel.GPT_4O: {"input": 0.005, "output": 0.015},
    AIModel.GPT_4O_MINI: {"input": 0.00015, "output": 0.0006},
    AIModel.GPT_35_TURBO: {"input": 0.0005, "output": 0.0015},
    AIModel.TEXT_EMBEDDING_ADA: {"input": 0.0001, "output": 0.0},
    AIModel.TEXT_EMBEDDING_3_SMALL: {"input": 0.00002, "output": 0.0},
    AIModel.TEXT_EMBEDDING_3_LARGE: {"input": 0.00013, "output": 0.0},

    # AWS Bedrock Claude (per 1K tokens)
    AIModel.CLAUDE_3_OPUS: {"input": 0.015, "output": 0.075},
    AIModel.CLAUDE_3_SONNET: {"input": 0.003, "output": 0.015},
    AIModel.CLAUDE_3_HAIKU: {"input": 0.00025, "output": 0.00125},
    AIModel.CLAUDE_35_SONNET: {"input": 0.003, "output": 0.015},
    AIModel.TITAN_TEXT: {"input": 0.0008, "output": 0.0016},
    AIModel.TITAN_EMBED: {"input": 0.0001, "output": 0.0},
}


class AIUsageRecord(BaseModel):
    """Single AI API usage record."""
    id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Provider and model
    provider: AIProvider
    model: str  # Model name/deployment
    model_id: Optional[AIModel] = None

    # Token counts
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    # Cost (calculated)
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0
    currency: str = "USD"

    # Context
    service_name: Optional[str] = None  # e.g., "claims_processor", "chat_agent"
    operation: Optional[str] = None  # e.g., "extract_invoice", "generate_response"
    request_id: Optional[str] = None
    user_id: Optional[str] = None

    # Performance
    latency_ms: Optional[int] = None

    def calculate_cost(self):
        """Calculate cost based on token counts and pricing."""
        if self.model_id and self.model_id in TOKEN_PRICING:
            pricing = TOKEN_PRICING[self.model_id]
            self.input_cost = round((self.input_tokens / 1000) * pricing["input"], 6)
            self.output_cost = round((self.output_tokens / 1000) * pricing["output"], 6)
            self.total_cost = round(self.input_cost + self.output_cost, 6)


class AIUsageSummary(BaseModel):
    """AI usage summary for a period."""
    period_start: date
    period_end: date

    # Total tokens
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0

    # Total cost
    total_cost: float = 0.0
    currency: str = "USD"

    # Breakdown by provider
    by_provider: Dict[str, Dict] = Field(default_factory=dict)
    # e.g., {"azure_openai": {"tokens": 1000000, "cost": 50.0}}

    # Breakdown by model
    by_model: Dict[str, Dict] = Field(default_factory=dict)
    # e.g., {"gpt-4": {"input_tokens": 500000, "output_tokens": 200000, "cost": 30.0}}

    # Breakdown by service/operation
    by_service: Dict[str, Dict] = Field(default_factory=dict)
    # e.g., {"claims_processor": {"tokens": 800000, "cost": 40.0}}

    # Request counts
    total_requests: int = 0
    requests_by_model: Dict[str, int] = Field(default_factory=dict)

    # Averages
    avg_tokens_per_request: float = 0.0
    avg_cost_per_request: float = 0.0
    avg_latency_ms: Optional[float] = None

    # Daily trend
    daily_usage: List[Dict] = Field(default_factory=list)
    # e.g., [{"date": "2024-01-15", "tokens": 50000, "cost": 2.50}]

    # Mock data indicator
    is_mock_data: bool = False


class DocumentIntelligenceUsage(BaseModel):
    """Document Intelligence (OCR) usage."""
    period_start: date
    period_end: date

    # Page counts
    total_pages_processed: int = 0
    pages_by_document_type: Dict[str, int] = Field(default_factory=dict)
    # e.g., {"vet_invoice": 500, "medical_record": 200}

    # Cost (Azure pricing: ~$1.50 per 1000 pages for prebuilt)
    cost_per_1000_pages: float = 1.50
    total_cost: float = 0.0
    currency: str = "USD"

    # Success/failure
    successful_extractions: int = 0
    failed_extractions: int = 0
    success_rate: float = 0.0


class DatabaseUsage(BaseModel):
    """Database (Cosmos DB) usage."""
    period_start: date
    period_end: date

    # Request Units
    total_ru_consumed: float = 0.0
    ru_by_operation: Dict[str, float] = Field(default_factory=dict)
    # e.g., {"read": 50000, "write": 20000, "query": 30000}

    # Storage
    storage_gb: float = 0.0

    # Cost
    total_cost: float = 0.0
    currency: str = "USD"


class PlatformUsageSummary(BaseModel):
    """Complete platform usage summary including all cost centers."""
    period_start: date
    period_end: date

    # AI/LLM Usage (biggest cost driver)
    ai_usage: Optional[AIUsageSummary] = None

    # Document Processing
    document_usage: Optional[DocumentIntelligenceUsage] = None

    # Database
    database_usage: Optional[DatabaseUsage] = None

    # Total costs by category
    cost_breakdown: Dict[str, float] = Field(default_factory=dict)
    # e.g., {"ai_llm": 500.0, "document_ocr": 50.0, "database": 100.0, "storage": 20.0}

    total_platform_cost: float = 0.0
    currency: str = "USD"

    # Comparison
    cost_change_vs_previous: Optional[float] = None
    cost_change_percent: Optional[float] = None

    # Mock data indicator
    is_mock_data: bool = False
