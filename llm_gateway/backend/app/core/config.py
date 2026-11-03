import os
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class TeamConfig(BaseModel):
    id: str
    name: str
    api_key: str
    rpm_limit: int = 60  # Requests per minute
    tpm_limit: int = 100000  # Tokens per minute
    monthly_budget_usd: float = 100.0
    current_spend_usd: float = 0.0
    allowed_tiers: List[str] = ["tier-premium", "tier-fast", "tier-economy"]
    system_prompt_override: Optional[str] = None
    priority: int = 1  # 1 (high), 2 (normal), 3 (low)

class ProviderModelPricing(BaseModel):
    input_cost_per_1k: float
    output_cost_per_1k: float

class Settings(BaseModel):
    app_name: str = "NexusGateway"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    
    # Redis configuration
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    
    # Model Tier Fallback Routing Chains
    fallback_chains: Dict[str, List[Dict[str, str]]] = Field(default_factory=lambda: {
        "tier-premium": [
            {"provider": "mock", "model": "mock-gpt-4o"},
            {"provider": "openai", "model": "gpt-4o"},
            {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
            {"provider": "ollama", "model": "llama3.2"}
        ],
        "tier-fast": [
            {"provider": "mock", "model": "mock-gpt-4o-mini"},
            {"provider": "openai", "model": "gpt-4o-mini"},
            {"provider": "anthropic", "model": "claude-3-5-haiku-20241022"},
            {"provider": "ollama", "model": "llama3.2"}
        ],
        "tier-economy": [
            {"provider": "mock", "model": "mock-llama3"},
            {"provider": "ollama", "model": "llama3.2"},
            {"provider": "openai", "model": "gpt-4o-mini"}
        ]
    })
    
    # Pricing reference ($ per 1,000 tokens)
    pricing: Dict[str, ProviderModelPricing] = Field(default_factory=lambda: {
        "gpt-4o": ProviderModelPricing(input_cost_per_1k=0.0025, output_cost_per_1k=0.010),
        "gpt-4o-mini": ProviderModelPricing(input_cost_per_1k=0.00015, output_cost_per_1k=0.0006),
        "claude-3-5-sonnet-20241022": ProviderModelPricing(input_cost_per_1k=0.003, output_cost_per_1k=0.015),
        "claude-3-5-haiku-20241022": ProviderModelPricing(input_cost_per_1k=0.0008, output_cost_per_1k=0.004),
        "llama3.2": ProviderModelPricing(input_cost_per_1k=0.0, output_cost_per_1k=0.0),
        "mock-gpt-4o": ProviderModelPricing(input_cost_per_1k=0.0025, output_cost_per_1k=0.010),
        "mock-gpt-4o-mini": ProviderModelPricing(input_cost_per_1k=0.00015, output_cost_per_1k=0.0006),
        "mock-llama3": ProviderModelPricing(input_cost_per_1k=0.0001, output_cost_per_1k=0.0002),
    })
    
    # Default Demo Teams
    teams: Dict[str, TeamConfig] = Field(default_factory=lambda: {
        "sk-team-alpha-key": TeamConfig(
            id="team-alpha",
            name="Engineering Alpha",
            api_key="sk-team-alpha-key",
            rpm_limit=120,
            tpm_limit=200000,
            monthly_budget_usd=500.0,
            current_spend_usd=42.50,
            priority=1
        ),
        "sk-team-beta-key": TeamConfig(
            id="team-beta",
            name="Product Analytics",
            api_key="sk-team-beta-key",
            rpm_limit=30,
            tpm_limit=50000,
            monthly_budget_usd=50.0,
            current_spend_usd=46.20, # Near 80% threshold
            priority=2
        ),
        "sk-team-gamma-key": TeamConfig(
            id="team-gamma",
            name="Batch Processing",
            api_key="sk-team-gamma-key",
            rpm_limit=10,
            tpm_limit=20000,
            monthly_budget_usd=20.0,
            current_spend_usd=20.0, # At 100% budget cap
            priority=3
        )
    })

settings = Settings()
