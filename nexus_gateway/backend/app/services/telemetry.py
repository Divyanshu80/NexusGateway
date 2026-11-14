import time
from typing import Dict, List, Any
from app.schemas.gateway import TelemetrySnapshot

class TelemetryService:
    def __init__(self):
        self.total_requests: int = 0
        self.successful_requests: int = 0
        self.failed_requests: int = 0
        self.total_tokens: int = 0
        self.total_cost_usd: float = 0.0
        self.latencies: List[float] = []
        self.total_fallbacks: int = 0
        self.request_logs: List[Dict[str, Any]] = []

    def record_request(
        self,
        team_id: str,
        requested_model: str,
        served_model: str,
        provider_served: str,
        status_code: int,
        latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        fallback_triggered: bool
    ):
        self.total_requests += 1
        if status_code == 200:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        tokens = prompt_tokens + completion_tokens
        self.total_tokens += tokens
        self.total_cost_usd = round(self.total_cost_usd + cost_usd, 6)
        
        if fallback_triggered:
            self.total_fallbacks += 1

        self.latencies.append(latency_ms)
        if len(self.latencies) > 500:
            self.latencies.pop(0)

        # Store recent request log
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "team_id": team_id,
            "requested_model": requested_model,
            "served_model": served_model,
            "provider_served": provider_served,
            "status_code": status_code,
            "latency_ms": round(latency_ms, 1),
            "total_tokens": tokens,
            "cost_usd": round(cost_usd, 6),
            "fallback_triggered": fallback_triggered
        }
        self.request_logs.insert(0, log_entry)
        if len(self.request_logs) > 100:
            self.request_logs.pop()

    def get_snapshot(self) -> TelemetrySnapshot:
        avg_lat = round(sum(self.latencies) / len(self.latencies), 1) if self.latencies else 0.0
        return TelemetrySnapshot(
            total_requests=self.total_requests,
            successful_requests=self.successful_requests,
            failed_requests=self.failed_requests,
            total_tokens=self.total_tokens,
            total_cost_usd=round(self.total_cost_usd, 4),
            avg_latency_ms=avg_lat,
            active_circuit_breakers=0,
            total_fallbacks=self.total_fallbacks
        )

    def get_prometheus_metrics(self) -> str:
        lines = [
            "# HELP nexus_gateway_requests_total Total HTTP requests processed",
            "# TYPE nexus_gateway_requests_total counter",
            f"nexus_gateway_requests_total{{status=\"success\"}} {self.successful_requests}",
            f"nexus_gateway_requests_total{{status=\"failed\"}} {self.failed_requests}",
            "",
            "# HELP nexus_gateway_tokens_total Total LLM tokens processed",
            "# TYPE nexus_gateway_tokens_total counter",
            f"nexus_gateway_tokens_total {self.total_tokens}",
            "",
            "# HELP nexus_gateway_cost_usd_total Total cost incurred in USD",
            "# TYPE nexus_gateway_cost_usd_total counter",
            f"nexus_gateway_cost_usd_total {self.total_cost_usd:.6f}",
            "",
            "# HELP nexus_gateway_fallback_total Total fallbacks triggered",
            "# TYPE nexus_gateway_fallback_total counter",
            f"nexus_gateway_fallback_total {self.total_fallbacks}"
        ]
        return "\n".join(lines) + "\n"

telemetry = TelemetryService()
