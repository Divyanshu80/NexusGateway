import time
import asyncio
from typing import Tuple, List, Dict, AsyncGenerator
from app.core.config import settings
from app.schemas.gateway import ChatCompletionRequest, ChatCompletionResponse
from app.providers.base import BaseLLMProvider
from app.providers.mock_provider import MockLLMProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.ollama_provider import OllamaProvider
from app.services.circuit_breaker import circuit_breaker_registry
from app.services.health_checker import health_checker
from app.services.budget_tracker import budget_tracker

class FallbackRouterService:
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {
            "mock": MockLLMProvider(),
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "ollama": OllamaProvider()
        }

    def get_provider(self, name: str) -> BaseLLMProvider:
        return self.providers.get(name, self.providers["mock"])

    def resolve_chain(self, requested_model_or_tier: str) -> List[Dict[str, str]]:
        # Check if requested model matches a predefined tier
        if requested_model_or_tier in settings.fallback_chains:
            return settings.fallback_chains[requested_model_or_tier]
        
        # Check if requested model belongs to mock/openai/anthropic/ollama directly
        if requested_model_or_tier.startswith("mock-"):
            return [{"provider": "mock", "model": requested_model_or_tier}]
        elif "gpt" in requested_model_or_tier:
            return [
                {"provider": "openai", "model": requested_model_or_tier},
                {"provider": "mock", "model": f"mock-{requested_model_or_tier}"},
                {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"}
            ]
        elif "claude" in requested_model_or_tier:
            return [
                {"provider": "anthropic", "model": requested_model_or_tier},
                {"provider": "mock", "model": "mock-gpt-4o"},
                {"provider": "openai", "model": "gpt-4o"}
            ]
        elif "llama" in requested_model_or_tier:
            return [
                {"provider": "ollama", "model": requested_model_or_tier},
                {"provider": "mock", "model": "mock-llama3"}
            ]
        
        # Default fallback chain
        return settings.fallback_chains["tier-fast"]

    async def execute_with_fallback(
        self,
        request: ChatCompletionRequest,
        team_id: str
    ) -> Tuple[ChatCompletionResponse, bool]:
        chain = self.resolve_chain(request.model)
        fallback_triggered = False
        last_exception = None

        for idx, step in enumerate(chain):
            provider_name = step["provider"]
            model_name = step["model"]

            if idx > 0:
                fallback_triggered = True

            cb = await circuit_breaker_registry.get_breaker(provider_name, model_name)
            allowed = await cb.allow_request()
            if not allowed:
                # Circuit open, skip to next in fallback chain
                continue

            provider_obj = self.get_provider(provider_name)
            
            # Retry loop with exponential backoff (up to 2 retries)
            for attempt in range(2):
                try:
                    res = await provider_obj.generate(request, model_name)
                    
                    # Record success in Circuit Breaker and Health Checker
                    await cb.record_success()
                    health_checker.record_call_result(provider_name, model_name, res.latency_ms, is_error=False)

                    # Compute cost and update response fields
                    cost_usd = budget_tracker.calculate_request_cost(
                        model_name,
                        res.usage.prompt_tokens,
                        res.usage.completion_tokens
                    )
                    res.cost_usd = cost_usd
                    res.fallback_triggered = fallback_triggered

                    # Record team spending
                    budget_tracker.record_spending(team_id, cost_usd)

                    return res, fallback_triggered
                except Exception as e:
                    last_exception = e
                    await cb.record_failure()
                    health_checker.record_call_result(provider_name, model_name, 0.0, is_error=True)
                    
                    # Exponential backoff delay for retries
                    if attempt < 1:
                        await asyncio.sleep(0.15 * (2 ** attempt))

        # All items in fallback chain failed
        raise RuntimeError(f"All LLM Providers in fallback chain failed. Last error: {str(last_exception)}")

    async def execute_stream_with_fallback(
        self,
        request: ChatCompletionRequest,
        team_id: str
    ) -> Tuple[AsyncGenerator[str, None], str, str]:
        chain = self.resolve_chain(request.model)
        last_exception = None

        for step in chain:
            provider_name = step["provider"]
            model_name = step["model"]

            cb = await circuit_breaker_registry.get_breaker(provider_name, model_name)
            allowed = await cb.allow_request()
            if not allowed:
                continue

            provider_obj = self.get_provider(provider_name)
            try:
                stream_gen = provider_obj.stream_generate(request, model_name)
                await cb.record_success()
                health_checker.record_call_result(provider_name, model_name, 50.0, is_error=False)
                return stream_gen, provider_name, model_name
            except Exception as e:
                last_exception = e
                await cb.record_failure()
                health_checker.record_call_result(provider_name, model_name, 0.0, is_error=True)

        raise RuntimeError(f"All LLM Providers in streaming fallback chain failed: {str(last_exception)}")

fallback_router = FallbackRouterService()
