import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  Zap,
  Activity,
  DollarSign,
  Layers,
  Server,
  Key,
  Terminal,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Play,
  ArrowRight,
  Cpu,
  Clock,
  Gauge
} from "lucide-react";
import {
  GATEWAY_BASE_URL,
  fetchHealthCheck,
  fetchTelemetrySummary,
  fetchProviderHealth,
  fetchTeams,
  fetchRecentLogs,
  toggleOutage
} from "./lib/gateway-api";

export default function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [isOnline, setIsOnline] = useState(false);
  const [telemetry, setTelemetry] = useState(null);
  const [healthList, setHealthList] = useState([]);
  const [teams, setTeams] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  // Playground state
  const [selectedApiKey, setSelectedApiKey] = useState("sk-team-alpha-key");
  const [selectedModel, setSelectedModel] = useState("tier-premium");
  const [promptInput, setPromptInput] = useState("Analyze server latency logs and summarize recent operational trends.");
  const [enableStream, setEnableStream] = useState(false);
  const [playgroundLoading, setPlaygroundLoading] = useState(false);
  const [playgroundResult, setPlaygroundResult] = useState(null);
  const [playgroundStreamOutput, setPlaygroundStreamOutput] = useState("");
  const [playgroundError, setPlaygroundError] = useState(null);

  const loadAllData = async () => {
    setLoading(true);
    const online = await fetchHealthCheck();
    setIsOnline(online);

    const [tel, health, tms, lg] = await Promise.all([
      fetchTelemetrySummary(),
      fetchProviderHealth(),
      fetchTeams(),
      fetchRecentLogs()
    ]);

    setTelemetry(tel);
    setHealthList(health);
    setTeams(tms);
    setLogs(lg);
    setLoading(false);
  };

  useEffect(() => {
    loadAllData();
    const interval = setInterval(loadAllData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleOutageToggle = async (model, currentActive) => {
    await toggleOutage(model, !currentActive);
    await loadAllData();
  };

  const handleRunPlayground = async () => {
    setPlaygroundLoading(true);
    setPlaygroundError(null);
    setPlaygroundResult(null);
    setPlaygroundStreamOutput("");

    try {
      if (enableStream) {
        const res = await fetch(`${GATEWAY_BASE_URL}/v1/chat/completions`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${selectedApiKey}`
          },
          body: JSON.stringify({
            model: selectedModel,
            messages: [{ role: "user", content: promptInput }],
            stream: true
          })
        });

        if (!res.ok) {
          const errText = await res.text();
          throw new Error(`HTTP ${res.status}: ${errText}`);
        }

        const reader = res.body?.getReader();
        const decoder = new TextDecoder();
        let accumulated = "";

        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value);
            accumulated += chunk;
            setPlaygroundStreamOutput(accumulated);
          }
        }
      } else {
        const res = await fetch(`${GATEWAY_BASE_URL}/v1/chat/completions`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${selectedApiKey}`
          },
          body: JSON.stringify({
            model: selectedModel,
            messages: [{ role: "user", content: promptInput }],
            stream: false
          })
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || `HTTP ${res.status}`);
        }
        setPlaygroundResult(data);
      }
      await loadAllData();
    } catch (err) {
      setPlaygroundError(err.message || "Request failed");
    } finally {
      setPlaygroundLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-cyan-500 selection:text-white pb-12">
      {/* Background Neon Grid Accent */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#1e293b15_1px,transparent_1px),linear-gradient(to_bottom,#1e293b15_1px,transparent_1px)] bg-[size:4rem_4rem] pointer-events-none" />

      {/* Header Bar */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-950/80 border-b border-slate-800/80 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Zap className="h-6 w-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                  NexusGateway
                </h1>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  React JS SPA
                </span>
              </div>
              <p className="text-xs text-slate-400">LLM API Gateway & Observability Dashboard</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Status indicator */}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium ${
              isOnline 
                ? "bg-emerald-950/40 text-emerald-400 border-emerald-500/30" 
                : "bg-amber-950/40 text-amber-400 border-amber-500/30"
            }`}>
              <span className={`h-2 w-2 rounded-full ${isOnline ? "bg-emerald-400 animate-pulse" : "bg-amber-400"}`} />
              {isOnline ? "FastAPI Connected (localhost:8000)" : "Fallback Demo Mode"}
            </div>

            <button
              onClick={loadAllData}
              className="p-2 text-slate-400 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg transition cursor-pointer"
              title="Refresh Telemetry"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-6 pt-6">
        <nav className="flex space-x-2 border-b border-slate-800/80 pb-3 overflow-x-auto">
          {[
            { id: "overview", label: "Overview & Telemetry", icon: Activity },
            { id: "playground", label: "Proxy Sandbox", icon: Terminal },
            { id: "budgets", label: "Rate Limits & Budgets", icon: ShieldAlert },
            { id: "resilience", label: "Resilience & Failover", icon: Layers },
            { id: "teams", label: "Teams & Keys", icon: Key },
            { id: "logs", label: "Request Logs", icon: Clock }
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg transition-all cursor-pointer whitespace-nowrap ${
                  isActive
                    ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Content Area */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* OVERVIEW TAB */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Top Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-semibold uppercase tracking-wider">Total Requests</span>
                  <Server className="h-4 w-4 text-cyan-400" />
                </div>
                <div className="text-2xl font-bold text-white">{telemetry?.total_requests ?? 0}</div>
                <div className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                  <span className="text-emerald-400 font-medium">{telemetry?.successful_requests ?? 0} success</span>
                  <span>•</span>
                  <span className="text-rose-400 font-medium">{telemetry?.failed_requests ?? 0} failed</span>
                </div>
              </div>

              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-semibold uppercase tracking-wider">Token Throughput</span>
                  <Cpu className="h-4 w-4 text-blue-400" />
                </div>
                <div className="text-2xl font-bold text-white">{(telemetry?.total_tokens ?? 0).toLocaleString()}</div>
                <div className="text-xs text-slate-400 mt-1">Input & Output Tokens</div>
              </div>

              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-semibold uppercase tracking-wider">Total Spend (USD)</span>
                  <DollarSign className="h-4 w-4 text-emerald-400" />
                </div>
                <div className="text-2xl font-bold text-emerald-400">${(telemetry?.total_cost_usd ?? 0).toFixed(4)}</div>
                <div className="text-xs text-slate-400 mt-1">Model Pricing Tracked</div>
              </div>

              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-semibold uppercase tracking-wider">Avg Latency & Fallbacks</span>
                  <Gauge className="h-4 w-4 text-purple-400" />
                </div>
                <div className="text-2xl font-bold text-white">{telemetry?.avg_latency_ms ?? 0} <span className="text-sm font-normal text-slate-400">ms</span></div>
                <div className="text-xs text-amber-400 mt-1 flex items-center gap-1 font-medium">
                  <Layers className="h-3 w-3" />
                  {telemetry?.total_fallbacks ?? 0} Automatic Failovers
                </div>
              </div>
            </div>

            {/* Provider Health Grid */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 backdrop-blur-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <Activity className="h-5 w-5 text-cyan-400" />
                    Live LLM Provider Health & Circuit Breakers
                  </h2>
                  <p className="text-xs text-slate-400">Continuous 30s background health checks & rolling P99 latency tracking</p>
                </div>
                <span className="text-xs text-slate-500">Auto-refresh 5s</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {healthList.map((hp, idx) => (
                  <div key={idx} className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <div className="font-semibold text-sm text-slate-200 uppercase tracking-wide">{hp.provider}</div>
                        <div className="text-xs text-cyan-400 font-mono">{hp.model}</div>
                      </div>
                      <div className={`px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 ${
                        hp.status === "HEALTHY"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : hp.status === "DEGRADED"
                          ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                      }`}>
                        {hp.status === "HEALTHY" && <CheckCircle2 className="h-3.5 w-3.5" />}
                        {hp.status === "DEGRADED" && <AlertTriangle className="h-3.5 w-3.5" />}
                        {hp.status === "DOWN" && <XCircle className="h-3.5 w-3.5" />}
                        {hp.status}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-900 font-mono">
                      <div>
                        <span className="text-slate-500">P99 Latency:</span>
                        <span className="ml-1 text-slate-200">{hp.p99_latency_ms} ms</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Error Rate:</span>
                        <span className="ml-1 text-slate-200">{hp.error_rate_pct}%</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Circuit:</span>
                        <span className={`ml-1 font-semibold ${
                          hp.circuit_state === "CLOSED" ? "text-emerald-400" : "text-rose-400"
                        }`}>{hp.circuit_state}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Last Ping:</span>
                        <span className="ml-1 text-slate-400">{hp.last_check}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Fallback Routing Chain Visualizer */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 backdrop-blur-sm">
              <h3 className="text-md font-bold text-white mb-3 flex items-center gap-2">
                <Layers className="h-4 w-4 text-purple-400" />
                Configured Multi-Provider Fallback Routing Chains
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
                  <div className="text-xs font-bold text-cyan-400 uppercase tracking-wider mb-2">Tier Premium</div>
                  <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
                    <span className="px-2 py-1 bg-slate-900 rounded border border-slate-800">mock-gpt-4o</span>
                    <ArrowRight className="h-3 w-3 text-slate-500" />
                    <span className="px-2 py-1 bg-slate-900 rounded border border-slate-800">gpt-4o</span>
                    <ArrowRight className="h-3 w-3 text-slate-500" />
                    <span className="px-2 py-1 bg-slate-900 rounded border border-slate-800">claude-3-5</span>
                  </div>
                </div>

                <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
                  <div className="text-xs font-bold text-blue-400 uppercase tracking-wider mb-2">Tier Fast</div>
                  <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
                    <span className="px-2 py-1 bg-slate-900 rounded border border-slate-800">mock-gpt-4o-mini</span>
                    <ArrowRight className="h-3 w-3 text-slate-500" />
                    <span className="px-2 py-1 bg-slate-900 rounded border border-slate-800">gpt-4o-mini</span>
                    <ArrowRight className="h-3 w-3 text-slate-500" />
                    <span className="px-2 py-1 bg-slate-900 rounded border border-slate-800">claude-haiku</span>
                  </div>
                </div>

                <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
                  <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2">Tier Economy</div>
                  <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
                    <span className="px-2 py-1 bg-slate-900 rounded border border-slate-800">mock-llama3</span>
                    <ArrowRight className="h-3 w-3 text-slate-500" />
                    <span className="px-2 py-1 bg-slate-900 rounded border border-slate-800">ollama/llama3.2</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* PLAYGROUND TAB */}
        {activeTab === "playground" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 backdrop-blur-sm space-y-4">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Terminal className="h-5 w-5 text-cyan-400" />
                  Proxy API Tester
                </h2>
                <p className="text-xs text-slate-400">Send requests through NexusGateway (/v1/chat/completions)</p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Select Team API Key
                </label>
                <select
                  value={selectedApiKey}
                  onChange={(e) => setSelectedApiKey(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
                >
                  {teams.map((t) => (
                    <option key={t.id} value={t.api_key}>
                      {t.name} ({t.api_key}) - Budget ${t.current_spend_usd.toFixed(2)} / ${t.monthly_budget_usd.toFixed(2)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Target Model / Tier
                </label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
                >
                  <option value="tier-premium">tier-premium (mock-gpt-4o &rarr; gpt-4o)</option>
                  <option value="tier-fast">tier-fast (mock-gpt-4o-mini &rarr; gpt-4o-mini)</option>
                  <option value="tier-economy">tier-economy (mock-llama3 &rarr; llama3.2)</option>
                  <option value="mock-gpt-4o">mock-gpt-4o (Direct Mock)</option>
                  <option value="gpt-4o">gpt-4o (OpenAI Live)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Prompt Input
                </label>
                <textarea
                  rows={4}
                  value={promptInput}
                  onChange={(e) => setPromptInput(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 resize-none font-mono"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={enableStream}
                    onChange={(e) => setEnableStream(e.target.checked)}
                    className="rounded bg-slate-950 border-slate-800 text-cyan-500 focus:ring-0"
                  />
                  Enable SSE Real-Time Streaming (`stream=true`)
                </label>

                <button
                  onClick={handleRunPlayground}
                  disabled={playgroundLoading}
                  className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-sm rounded-lg shadow-lg shadow-cyan-500/20 transition disabled:opacity-50 cursor-pointer"
                >
                  <Play className="h-4 w-4 fill-white" />
                  {playgroundLoading ? "Proxying..." : "Send Request"}
                </button>
              </div>
            </div>

            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 backdrop-blur-sm space-y-4">
              <h3 className="text-md font-bold text-white flex items-center justify-between">
                <span>Gateway Response & Metadata</span>
                {playgroundResult && (
                  <span className="text-xs px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full font-mono">
                    HTTP 200 OK
                  </span>
                )}
              </h3>

              {playgroundError && (
                <div className="p-4 bg-rose-950/50 border border-rose-800 rounded-lg text-xs text-rose-300 font-mono space-y-1">
                  <div className="font-bold text-rose-200 flex items-center gap-2">
                    <XCircle className="h-4 w-4 text-rose-400" />
                    Gateway Rejected Request
                  </div>
                  <div>{playgroundError}</div>
                </div>
              )}

              {playgroundResult && (
                <div className="space-y-3">
                  <div className="grid grid-cols-3 gap-2 bg-slate-950/80 p-3 rounded-lg border border-slate-800/80 text-xs font-mono">
                    <div>
                      <span className="text-slate-500 block">Provider Served:</span>
                      <span className="text-cyan-400 font-bold">{playgroundResult.provider_served}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Model Served:</span>
                      <span className="text-slate-200">{playgroundResult.model}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Cost (USD):</span>
                      <span className="text-emerald-400 font-bold">${playgroundResult.cost_usd?.toFixed(6) ?? "0.000000"}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Latency:</span>
                      <span className="text-slate-200">{playgroundResult.latency_ms} ms</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Total Tokens:</span>
                      <span className="text-slate-200">{playgroundResult.usage?.total_tokens}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Fallback Triggered:</span>
                      <span className={playgroundResult.fallback_triggered ? "text-amber-400 font-bold" : "text-slate-400"}>
                        {playgroundResult.fallback_triggered ? "YES" : "NO"}
                      </span>
                    </div>
                  </div>

                  <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 font-mono text-xs text-slate-200 whitespace-pre-wrap leading-relaxed max-h-64 overflow-y-auto">
                    {playgroundResult.choices?.[0]?.message?.content}
                  </div>
                </div>
              )}

              {enableStream && playgroundStreamOutput && (
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">
                    Raw SSE Stream Chunks
                  </div>
                  <pre className="bg-slate-950 p-4 rounded-lg border border-slate-800 font-mono text-xs text-cyan-300 whitespace-pre-wrap max-h-64 overflow-y-auto">
                    {playgroundStreamOutput}
                  </pre>
                </div>
              )}

              {!playgroundResult && !playgroundError && !playgroundStreamOutput && (
                <div className="h-64 flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-lg text-slate-500 text-xs gap-2">
                  <Terminal className="h-8 w-8 text-slate-600" />
                  <span>Click &quot;Send Request&quot; to observe real-time Gateway headers, cost calculation, and provider routing.</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* RATE LIMITS & BUDGETS TAB */}
        {activeTab === "budgets" && (
          <div className="space-y-6">
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 backdrop-blur-sm">
              <h2 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-amber-400" />
                Team Rate Limits & Budget Caps
              </h2>
              <p className="text-xs text-slate-400 mb-6">
                Distributed Token Bucket (RPM/TPM) enforcement & dynamic USD budget thresholds
              </p>

              <div className="space-y-4">
                {teams.map((t) => {
                  const usedPct = t.budget_used_percentage;
                  const isBlocked = usedPct >= 100.0;
                  const isWarning = usedPct >= 80.0 && !isBlocked;

                  return (
                    <div key={t.id} className="bg-slate-950/80 border border-slate-800 rounded-lg p-5">
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-bold text-md text-white">{t.name}</h3>
                            <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                              {t.id}
                            </span>
                            <span className="text-xs font-mono text-slate-400">
                              Priority: P{t.priority}
                            </span>
                          </div>
                          <div className="text-xs text-slate-400 mt-1 font-mono">
                            API Key: <span className="text-slate-200">{t.api_key}</span>
                          </div>
                        </div>

                        <div>
                          {isBlocked && (
                            <span className="px-3 py-1 bg-rose-500/10 text-rose-400 border border-rose-500/30 rounded-full text-xs font-bold flex items-center gap-1.5">
                              <XCircle className="h-3.5 w-3.5" />
                              BUDGET CAP EXCEEDED (HTTP 402 BLOCKED)
                            </span>
                          )}
                          {isWarning && (
                            <span className="px-3 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/30 rounded-full text-xs font-bold flex items-center gap-1.5">
                              <AlertTriangle className="h-3.5 w-3.5" />
                              BUDGET WARNING (80%+ THRESHOLD)
                            </span>
                          )}
                          {!isBlocked && !isWarning && (
                            <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full text-xs font-bold flex items-center gap-1.5">
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              ACTIVE & WITHIN LIMITS
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="space-y-1 mb-3">
                        <div className="flex justify-between text-xs font-mono">
                          <span className="text-slate-400">USD Monthly Spend</span>
                          <span className="text-slate-200">
                            ${t.current_spend_usd.toFixed(2)} / ${t.monthly_budget_usd.toFixed(2)} ({usedPct.toFixed(1)}%)
                          </span>
                        </div>
                        <div className="h-2.5 w-full bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                          <div
                            className={`h-full transition-all ${
                              isBlocked ? "bg-rose-500" : isWarning ? "bg-amber-400" : "bg-cyan-500"
                            }`}
                            style={{ width: `${Math.min(100, usedPct)}%` }}
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs pt-3 border-t border-slate-900/80 font-mono text-slate-400">
                        <div>
                          <span>RPM Limit:</span> <strong className="text-slate-200">{t.rpm_limit} req/min</strong>
                        </div>
                        <div>
                          <span>TPM Limit:</span> <strong className="text-slate-200">{t.tpm_limit.toLocaleString()} tok/min</strong>
                        </div>
                        <div className="col-span-2">
                          <span>Allowed Tiers:</span>{" "}
                          <span className="text-cyan-400">{t.allowed_tiers.join(", ")}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* RESILIENCE TAB */}
        {activeTab === "resilience" && (
          <div className="space-y-6">
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 backdrop-blur-sm">
              <div className="mb-6">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Layers className="h-5 w-5 text-purple-400" />
                  Circuit Breaker & Outage Simulator
                </h2>
                <p className="text-xs text-slate-400">
                  Toggle simulated outages to verify automatic fallback routing and circuit breaker state transitions in real-time.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  { model: "mock-gpt-4o", label: "Mock Primary (mock-gpt-4o)" },
                  { model: "mock-gpt-4o-mini", label: "Mock Fast (mock-gpt-4o-mini)" },
                  { model: "mock-llama3", label: "Mock Economy (mock-llama3)" },
                ].map((item) => {
                  const statusObj = healthList.find((h) => h.model === item.model);
                  const isDown = statusObj?.status === "DOWN" || statusObj?.circuit_state === "OPEN";

                  return (
                    <div key={item.model} className="bg-slate-950/80 border border-slate-800 rounded-lg p-5 flex items-center justify-between">
                      <div>
                        <div className="font-bold text-sm text-slate-200">{item.label}</div>
                        <div className="text-xs text-slate-400 font-mono mt-1">
                          Circuit State: <span className={isDown ? "text-rose-400 font-bold" : "text-emerald-400"}>{statusObj?.circuit_state || "CLOSED"}</span>
                        </div>
                      </div>

                      <button
                        onClick={() => handleOutageToggle(item.model, isDown)}
                        className={`px-4 py-2 rounded-lg text-xs font-semibold transition cursor-pointer ${
                          isDown
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-500/30"
                            : "bg-rose-500/20 text-rose-300 border border-rose-500/40 hover:bg-rose-500/30"
                        }`}
                      >
                        {isDown ? "Restore Service" : "Simulate Outage"}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* TEAMS TAB */}
        {activeTab === "teams" && (
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 backdrop-blur-sm">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Key className="h-5 w-5 text-cyan-400" />
              Team API Key Directory
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300 font-mono">
                <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="p-3">Team Name</th>
                    <th className="p-3">Team ID</th>
                    <th className="p-3">API Key</th>
                    <th className="p-3">Priority</th>
                    <th className="p-3">Spend (USD)</th>
                    <th className="p-3">Budget Cap</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {teams.map((t) => (
                    <tr key={t.id} className="hover:bg-slate-950/40">
                      <td className="p-3 font-bold text-white">{t.name}</td>
                      <td className="p-3 text-cyan-400">{t.id}</td>
                      <td className="p-3 text-slate-400">{t.api_key}</td>
                      <td className="p-3">Priority {t.priority}</td>
                      <td className="p-3 text-emerald-400">${t.current_spend_usd.toFixed(2)}</td>
                      <td className="p-3">${t.monthly_budget_usd.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* LOGS TAB */}
        {activeTab === "logs" && (
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Clock className="h-5 w-5 text-cyan-400" />
                Live Request Stream & OpenTelemetry Traces
              </h2>
              <span className="text-xs text-slate-400">{logs.length} Recent Requests</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300 font-mono">
                <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="p-3">Timestamp</th>
                    <th className="p-3">Team</th>
                    <th className="p-3">Req Model</th>
                    <th className="p-3">Served Model</th>
                    <th className="p-3">Provider</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Latency</th>
                    <th className="p-3">Tokens</th>
                    <th className="p-3">Cost ($)</th>
                    <th className="p-3">Fallback</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {logs.map((lg, i) => (
                    <tr key={i} className="hover:bg-slate-950/40">
                      <td className="p-3 text-slate-400">{lg.timestamp}</td>
                      <td className="p-3 text-slate-200">{lg.team_id}</td>
                      <td className="p-3 text-cyan-400">{lg.requested_model}</td>
                      <td className="p-3 text-slate-300">{lg.served_model}</td>
                      <td className="p-3 uppercase text-slate-400">{lg.provider_served}</td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          lg.status_code === 200 ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
                        }`}>
                          {lg.status_code}
                        </span>
                      </td>
                      <td className="p-3 text-slate-300">{lg.latency_ms} ms</td>
                      <td className="p-3 text-slate-300">{lg.total_tokens}</td>
                      <td className="p-3 text-emerald-400">${lg.cost_usd.toFixed(6)}</td>
                      <td className="p-3">
                        {lg.fallback_triggered ? (
                          <span className="px-2 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/30 rounded text-[10px] font-bold">
                            TRIGGERED
                          </span>
                        ) : (
                          <span className="text-slate-500">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
