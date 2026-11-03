import time
import asyncio
from typing import Dict, List, Any
from app.schemas.gateway import ProviderHealthStatus
from app.services.circuit_breaker import circuit_breaker_registry

class HealthCheckerService:
    def __init__(self):
        # Key: "provider:model" -> list of latency samples
        self._latencies: Dict[str, List[float]] = {}
        self._errors: Dict[str, int] = {}
        self._total_calls: Dict[str, int] = {}
        self._last_checked: Dict[str, float] = {}

    def record_call_result(self, provider: str, model: str, latency_ms: float, is_error: bool):
        key = f"{provider}:{model}"
        if key not in self._latencies:
            self._latencies[key] = []
            self._errors[key] = 0
            self._total_calls[key] = 0
        
        self._total_calls[key] += 1
        if is_error:
            self._errors[key] += 1
        else:
            self._latencies[key].append(latency_ms)
            # Keep rolling window of last 100 calls
            if len(self._latencies[key]) > 100:
                self._latencies[key].pop(0)
        
        self._last_checked[key] = time.time()

    async def get_health_statuses(self) -> List[ProviderHealthStatus]:
        states = await circuit_breaker_registry.get_all_states()
        
        known_targets = [
            ("mock", "mock-gpt-4o"),
            ("mock", "mock-gpt-4o-mini"),
            ("mock", "mock-llama3"),
            ("openai", "gpt-4o"),
            ("openai", "gpt-4o-mini"),
            ("anthropic", "claude-3-5-sonnet-20241022"),
            ("anthropic", "claude-3-5-haiku-20241022"),
            ("ollama", "llama3.2"),
        ]

        result = []
        for provider, model in known_targets:
            key = f"{provider}:{model}"
            cb_state = states.get(key, "CLOSED")
            
            lats = self._latencies.get(key, [85.0])
            if lats:
                sorted_lats = sorted(lats)
                p99_idx = int(len(sorted_lats) * 0.99)
                p99 = round(sorted_lats[min(p99_idx, len(sorted_lats) - 1)], 1)
            else:
                p99 = 0.0

            total = self._total_calls.get(key, 0)
            errs = self._errors.get(key, 0)
            err_pct = round((errs / total * 100.0), 1) if total > 0 else 0.0

            if cb_state == "OPEN":
                status = "DOWN"
            elif err_pct > 15.0 or p99 > 2500.0:
                status = "DEGRADED"
            else:
                status = "HEALTHY"

            result.append(
                ProviderHealthStatus(
                    provider=provider,
                    model=model,
                    status=status,
                    p99_latency_ms=p99,
                    error_rate_pct=err_pct,
                    last_check=time.strftime("%H:%M:%S", time.localtime(self._last_checked.get(key, time.time()))),
                    circuit_state=cb_state
                )
            )
        return result

health_checker = HealthCheckerService()
