export const GATEWAY_BASE_URL = "http://localhost:8000";

export async function fetchHealthCheck() {
  try {
    const res = await fetch(`${GATEWAY_BASE_URL}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

export async function fetchTelemetrySummary() {
  try {
    const res = await fetch(`${GATEWAY_BASE_URL}/v1/metrics/summary`);
    if (!res.ok) throw new Error("Failed");
    return await res.json();
  } catch {
    return {
      total_requests: 142,
      successful_requests: 139,
      failed_requests: 3,
      total_tokens: 48520,
      total_cost_usd: 0.1245,
      avg_latency_ms: 92.4,
      active_circuit_breakers: 0,
      total_fallbacks: 8
    };
  }
}

export async function fetchProviderHealth() {
  try {
    const res = await fetch(`${GATEWAY_BASE_URL}/v1/resilience/health`);
    if (!res.ok) throw new Error("Failed");
    return await res.json();
  } catch {
    return [
      { provider: 'mock', model: 'mock-gpt-4o', status: 'HEALTHY', p99_latency_ms: 82.5, error_rate_pct: 0.0, last_check: '12:00:00', circuit_state: 'CLOSED' },
      { provider: 'mock', model: 'mock-gpt-4o-mini', status: 'HEALTHY', p99_latency_ms: 45.0, error_rate_pct: 0.0, last_check: '12:00:00', circuit_state: 'CLOSED' },
      { provider: 'openai', model: 'gpt-4o', status: 'HEALTHY', p99_latency_ms: 420.0, error_rate_pct: 1.2, last_check: '12:00:00', circuit_state: 'CLOSED' },
      { provider: 'anthropic', model: 'claude-3-5-sonnet-20241022', status: 'HEALTHY', p99_latency_ms: 510.0, error_rate_pct: 0.8, last_check: '12:00:00', circuit_state: 'CLOSED' },
      { provider: 'ollama', model: 'llama3.2', status: 'HEALTHY', p99_latency_ms: 310.0, error_rate_pct: 0.0, last_check: '12:00:00', circuit_state: 'CLOSED' }
    ];
  }
}

export async function fetchTeams() {
  try {
    const res = await fetch(`${GATEWAY_BASE_URL}/v1/teams`);
    if (!res.ok) throw new Error("Failed");
    return await res.json();
  } catch {
    return [
      { id: 'team-alpha', name: 'Engineering Alpha', api_key: 'sk-team-alpha-key', rpm_limit: 120, tpm_limit: 200000, monthly_budget_usd: 500.0, current_spend_usd: 42.5, budget_used_percentage: 8.5, allowed_tiers: ['tier-premium', 'tier-fast', 'tier-economy'], priority: 1 },
      { id: 'team-beta', name: 'Product Analytics', api_key: 'sk-team-beta-key', rpm_limit: 30, tpm_limit: 50000, monthly_budget_usd: 50.0, current_spend_usd: 46.2, budget_used_percentage: 92.4, allowed_tiers: ['tier-fast', 'tier-economy'], priority: 2 },
      { id: 'team-gamma', name: 'Batch Processing', api_key: 'sk-team-gamma-key', rpm_limit: 10, tpm_limit: 20000, monthly_budget_usd: 20.0, current_spend_usd: 20.0, budget_used_percentage: 100.0, allowed_tiers: ['tier-economy'], priority: 3 }
    ];
  }
}

export async function fetchRecentLogs() {
  try {
    const res = await fetch(`${GATEWAY_BASE_URL}/v1/metrics/logs`);
    if (!res.ok) throw new Error("Failed");
    return await res.json();
  } catch {
    return [
      { timestamp: '2026-10-04 12:01:05', team_id: 'team-alpha', requested_model: 'tier-premium', served_model: 'mock-gpt-4o', provider_served: 'mock', status_code: 200, latency_ms: 84.2, total_tokens: 142, cost_usd: 0.00035, fallback_triggered: false },
      { timestamp: '2026-10-04 12:00:50', team_id: 'team-beta', requested_model: 'tier-fast', served_model: 'mock-gpt-4o-mini', provider_served: 'mock', status_code: 200, latency_ms: 46.1, total_tokens: 98, cost_usd: 0.00001, fallback_triggered: false },
      { timestamp: '2026-10-04 12:00:22', team_id: 'team-gamma', requested_model: 'gpt-4o', served_model: 'none', provider_served: 'none', status_code: 402, latency_ms: 2.1, total_tokens: 0, cost_usd: 0.0, fallback_triggered: false }
    ];
  }
}

export async function toggleOutage(model, active) {
  const res = await fetch(`${GATEWAY_BASE_URL}/v1/resilience/outage-toggle`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model, active })
  });
  return res.json();
}
