from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = Field(default="gpt-4o-mini", description="Target model or tier (e.g. tier-fast, gpt-4o)")
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500
    stream: Optional[bool] = False
    top_p: Optional[float] = 1.0

class UsageInfo(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChoiceDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None

class ChoiceStream(BaseModel):
    index: int = 0
    delta: ChoiceDelta
    finish_reason: Optional[str] = None

class Choice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: Optional[str] = "stop"

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    provider_served: str
    choices: List[Choice]
    usage: UsageInfo
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    fallback_triggered: bool = False

class TeamResponse(BaseModel):
    id: str
    name: str
    api_key: str
    rpm_limit: int
    tpm_limit: int
    monthly_budget_usd: float
    current_spend_usd: float
    budget_used_percentage: float
    allowed_tiers: List[str]
    priority: int

class ProviderHealthStatus(BaseModel):
    provider: str
    model: str
    status: str  # HEALTHY, DEGRADED, DOWN
    p99_latency_ms: float
    error_rate_pct: float
    last_check: str
    circuit_state: str  # CLOSED, OPEN, HALF_OPEN

class TelemetrySnapshot(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens: int
    total_cost_usd: float
    avg_latency_ms: float
    active_circuit_breakers: int
    total_fallbacks: int
