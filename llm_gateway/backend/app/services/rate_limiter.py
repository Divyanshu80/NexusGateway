import time
import asyncio
from typing import Tuple, Dict
from app.core.config import TeamConfig, settings

class TokenBucket:
    def __init__(self, capacity: int, refill_rate_per_sec: float):
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.refill_rate = refill_rate_per_sec
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def consume(self, amount: int = 1) -> Tuple[bool, float]:
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.last_update = now
            
            # Refill tokens
            self.tokens = min(self.capacity, self.tokens + (elapsed * self.refill_rate))
            
            if self.tokens >= amount:
                self.tokens -= amount
                return True, 0.0
            else:
                needed = amount - self.tokens
                retry_after = needed / self.refill_rate if self.refill_rate > 0 else 60.0
                return False, round(retry_after, 2)

class RateLimiterService:
    def __init__(self):
        # Local in-memory buckets for zero-dependency execution
        # Key: (team_id, "rpm" | "tpm")
        self._buckets: Dict[Tuple[str, str], TokenBucket] = {}
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, team: TeamConfig, token_estimate: int = 50) -> Tuple[bool, str, float]:
        """
        Returns (allowed: bool, reason: str, retry_after: float)
        """
        now = time.time()
        
        # RPM Bucket
        rpm_key = (team.id, "rpm")
        if rpm_key not in self._buckets:
            # Capacity = RPM, refill rate = RPM / 60.0 per sec
            self._buckets[rpm_key] = TokenBucket(team.rpm_limit, team.rpm_limit / 60.0)
            
        allowed_rpm, retry_rpm = await self._buckets[rpm_key].consume(1)
        if not allowed_rpm:
            return False, f"Rate limit exceeded (RPM Limit: {team.rpm_limit})", retry_rpm

        # TPM Bucket
        tpm_key = (team.id, "tpm")
        if tpm_key not in self._buckets:
            # Capacity = TPM, refill rate = TPM / 60.0 per sec
            self._buckets[tpm_key] = TokenBucket(team.tpm_limit, team.tpm_limit / 60.0)

        allowed_tpm, retry_tpm = await self._buckets[tpm_key].consume(token_estimate)
        if not allowed_tpm:
            return False, f"Token rate limit exceeded (TPM Limit: {team.tpm_limit})", retry_tpm

        return True, "OK", 0.0

rate_limiter = RateLimiterService()
