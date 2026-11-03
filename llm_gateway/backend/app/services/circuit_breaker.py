import time
import asyncio
from typing import Dict

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 15.0):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        
        # State: "CLOSED" (normal), "OPEN" (tripped), "HALF_OPEN" (testing)
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_state_change = time.time()
        self.last_failure_time = 0.0
        self._lock = asyncio.Lock()

    async def allow_request(self) -> bool:
        async with self._lock:
            now = time.time()
            if self.state == "OPEN":
                if now - self.last_state_change >= self.cooldown_seconds:
                    self.state = "HALF_OPEN"
                    self.last_state_change = now
                    return True  # Allow trial request
                return False  # Block request while open
            return True

    async def record_success(self):
        async with self._lock:
            self.failure_count = 0
            if self.state != "CLOSED":
                self.state = "CLOSED"
                self.last_state_change = time.time()

    async def record_failure(self):
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                if self.state != "OPEN":
                    self.state = "OPEN"
                    self.last_state_change = time.time()

class CircuitBreakerRegistry:
    def __init__(self):
        # Key: (provider_name, model_name)
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    def _get_key(self, provider: str, model: str) -> str:
        return f"{provider}:{model}"

    async def get_breaker(self, provider: str, model: str) -> CircuitBreaker:
        key = self._get_key(provider, model)
        if key not in self._breakers:
            async with self._lock:
                if key not in self._breakers:
                    self._breakers[key] = CircuitBreaker()
        return self._breakers[key]

    async def get_all_states(self) -> Dict[str, str]:
        res = {}
        for key, cb in self._breakers.items():
            res[key] = cb.state
        return res

circuit_breaker_registry = CircuitBreakerRegistry()
