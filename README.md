# NexusGateway

Production-grade LLM proxy and observability platform: unified OpenAI-compatible routing, token bucket rate limiting (RPM/TPM), multi-tenant budget caps, circuit breaker failover routing, and real-time telemetry dashboard.

---

## Project architecture

<img width="1752" height="897" alt="NexusGateway LLM Architecture Infographic" src="https://github.com/user-attachments/assets/ac8410c1-12c4-4aff-b4c5-07a9223797e0" />

---

## Tech stack

* **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic v2, HTTPX
* **Frontend:** React 19, Vite, Tailwind CSS v4, Lucide Icons
* **Gateway & Governance:** Distributed Token Bucket Rate Limiter (RPM & TPM), Dynamic USD Monthly Budget Caps (HTTP 402), Multi-Tenant Team API Keys
* **Resilience & Failover:** Circuit Breaker Pattern (`CLOSED`, `OPEN`, `HALF-OPEN`), Multi-Tier Fallback Chains (`tier-premium`, `tier-fast`, `tier-economy`), Outage Simulator
* **Streaming & Transport:** Server-Sent Events (SSE) streaming (`stream=true`), HTTP/1.1 chunked transfer
* **Observability:** Prometheus scraping endpoint (`/metrics`), live health check worker, per-request latency, token, and USD cost tracking

---

## Setup and run

### Prerequisites
* Python 3.10 or higher
* Node.js 18+ and npm

### Quick start (single command)

Clone the repository and run the launcher script:

```bash
git clone https://github.com/Divyanshu80/NexusGateway.git
cd NexusGateway/nexus_gateway

# Make launcher executable and run
chmod +x start_local.sh
./start_local.sh
```

### Manual setup

If you prefer starting backend and frontend independently:

#### 1. Backend (FastAPI Gateway)
```bash
cd nexus_gateway/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend (React 19 Dashboard)
```bash
cd nexus_gateway/frontend
npm install
npm run dev
```

---

## Service URLs

| Service | URL | Description |
| :--- | :--- | :--- |
| **Gateway API** | [http://localhost:8000](http://localhost:8000) | Root service & proxy endpoint |
| **API Docs (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive OpenAPI documentation |
| **Observability Dashboard** | [http://localhost:3000](http://localhost:3000) | React 19 Real-Time Telemetry & Management UI |
| **Prometheus Metrics** | [http://localhost:8000/metrics](http://localhost:8000/metrics) | Standard Prometheus scrape target |

---

## First use

1. **Open the Dashboard:** Go to [http://localhost:3000](http://localhost:3000) to inspect system health, active circuit breakers, and total spend.
2. **Interactive Testing (Playground):**
   * Open the **Playground** tab.
   * Select **Engineering Alpha** (`sk-team-alpha-key`) and target tier `tier-premium`.
   * Click **Send Request** (or toggle **Enable SSE Streaming**) to inspect returned response headers, latency (ms), token usage, and cost calculation.
3. **Simulate Outage & Automatic Failover:**
   * Go to the **Resilience & Failover** tab.
   * Click **Simulate Outage** on `mock-gpt-4o` (circuit transitions to `OPEN`).
   * Switch back to the **Playground** and send another prompt targeting `tier-premium`.
   * **Result:** The gateway automatically reroutes to the next provider in the chain without failing the client. The response badge highlights `Fallback Triggered: YES`.
4. **Budget Cap Enforcement:**
   * Switch the API key in the Playground to **Batch Processing** (`sk-team-gamma-key`).
   * Send a request: the gateway instantly blocks the request with **HTTP 402 Payment Required** because Team Gamma has consumed 100% of their monthly budget.

---

## Environment variables

See [.env.example](.env.example). Important configuration keys:

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `PORT` | `8000` | Gateway HTTP server port |
| `REDIS_URL` | `redis://localhost:6379/0` | Optional Redis URL for distributed rate limiting |
| `OPENAI_API_KEY` | *(empty)* | Optional API key for live OpenAI model routing |
| `ANTHROPIC_API_KEY` | *(empty)* | Optional API key for live Anthropic model routing |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Optional local Ollama endpoint for local model routing |

---

## Using with OpenAI SDK (Drop-In Replacement)

NexusGateway is 100% compatible with existing OpenAI clients. Simply change the `base_url`:

```python
from openai import OpenAI

# Initialize client pointing to NexusGateway
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="sk-team-alpha-key"  # Authenticated team API key
)

# Standard completion with automatic fallback and cost tracking
response = client.chat.completions.create(
    model="tier-premium",  # tier-premium routes: mock-gpt-4o -> gpt-4o -> claude-3-5
    messages=[
        {"role": "user", "content": "Explain circuit breaker pattern in distributed systems."}
    ],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Direct cURL Request
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-team-alpha-key" \
  -d '{
    "model": "tier-fast",
    "messages": [{"role": "user", "content": "Ping gateway health"}],
    "stream": false
  }'
```
