# SentinelAI

SentinelAI is an AI observability platform designed to provide **end-to-end visibility into AI application execution**.

It provides a language-neutral execution protocol, a Python SDK for instrumentation, an optional platform for persistence and APIs, and reference/customer runtimes that consume these capabilities independently.

## Architecture

SentinelAI is composed of four independently deployable/usable layers:

1. **Execution Protocol** — Language-neutral contracts and event definitions for AI execution.
2. **Python SDK** — Lightweight SDK for instrumenting AI applications.
3. **Platform** — Optional backend providing APIs, persistence, and storage.
4. **Customer Runtime** — Application/runtime that integrates the SDK and optionally the Platform.

The SDK remains completely independent from the Platform and runtime implementations.

---

## Features

* Language-neutral execution protocol
* Lightweight Python SDK
* Execution and stage-level tracing
* Correlation IDs for distributed execution tracking
* Automatic execution lifecycle management
* Event-based execution publishing
* Pydantic-based contracts and validation
* Pluggable execution streams
* Optional PostgreSQL persistence
* Optional FastAPI backend
* Reference runtime for local development
* Extensible plugin architecture

---

## Project Structure

```text
SentinelAI/
├── sentinelai/                       # Core Python SDK
│   ├── contracts/                    # Public data contracts
│   ├── execution/                    # Execution lifecycle
│   ├── tracing/                      # Tracing and spans
│   ├── execution_stream/             # Event publishing
│   └── plugins/                      # SDK plugins
│
├── sentinelai_platform/              # Optional platform backend
│   ├── api/                           # API layer
│   ├── execution_store/              # Execution persistence
│   ├── event_subscribers/            # Event subscribers
│   └── persistence/                  # Database/storage
│
├── protocol/                          # Language-neutral protocol
│
├── examples/
│   └── reference_runtime/            # Demo/customer runtime
│
├── docs/                              # Architecture and API docs
│
├── tests/                             # Test suite
│
└── alembic.ini                        # Database migrations
```

---

## Installation

### Core SDK

Install the lightweight SDK with only its core dependencies:

```bash
uv add sentinelai
```

The core SDK is intentionally lightweight and does not depend on FastAPI, SQLAlchemy, PostgreSQL, Supabase, or the reference runtime.

### Platform

Install the optional Platform components when persistence and APIs are required:

```bash
uv add "sentinelai[platform]"
```

### Development / Reference Runtime

To work with the repository locally:

```bash
uv sync --extra reference --extra dev
```

---

## Minimal Instrumentation

Customer applications only need to annotate their execution and stage boundaries.

```python
from sentinelai import Contracts, configure, execution, span
from sentinelai.execution_stream import InMemoryExecutionStream


configure(
    publisher=InMemoryExecutionStream(),
    model_info=Contracts.ModelInfo(
        provider="acme",
        model_name="demo",
    ),
)


@span("my_stage")
async def run_stage(query: str) -> dict[str, str]:
    return {"answer": "ok"}


@execution("query")
async def main(query: str) -> dict[str, str]:
    return await run_stage(query)
```

The customer owns the business logic.

SentinelAI manages:

* Execution lifecycle
* Trace creation
* Stage lifecycle
* Correlation context
* Event creation
* Event publication
* Stage inference
* Execution metadata

---

## Execution Flow

```text
Customer Application
        │
        ▼
   @execution
        │
        ├───────────────┐
        ▼               ▼
    @span            @span
   Stage A           Stage B
        │               │
        └───────┬───────┘
                ▼
        Execution Events
                │
                ▼
       ExecutionStream
                │
        ┌───────┴────────┐
        ▼                ▼
   In-Memory         Platform
     Stream          Persistence
                         │
                         ▼
                    PostgreSQL
```

This separation allows the SDK to be used independently from the persistence and analytics layers.

---

## Platform Persistence

Applications that require persistent execution data can opt into the Platform.

```python
from sentinelai_platform.event_subscribers import (
    register_persistence_subscribers,
)

from sentinelai_platform.execution_store import (
    TracePersister,
)

from sentinelai_platform.persistence.postgres import (
    PostgresExecutionSnapshotRepository,
)
```

The Platform consumes execution events published by the SDK and projects them into persistent storage.

The core SDK **does not import or depend on**:

```text
sentinelai_platform
FastAPI
SQLAlchemy
Supabase
Reference Runtime
```

This keeps the SDK lightweight and allows the Platform to evolve independently.

---

## Public API

The following exports form the stable public API of `sentinelai`:

```python
Sentinel
configure
execution
span
ExecutionStream
Contracts
Plugin
```

The SDK also exposes ambient correlation/context getters for retrieving the current execution context.

For detailed API information, see:

* `docs/public-api.md`
* `docs/architecture.md`
* `protocol/README.md`

---

## Execution Protocol

The Execution Protocol defines the language-neutral representation of AI application execution.

It provides standardized concepts for:

* Executions
* Stages
* Events
* Correlation
* Model metadata
* Execution status
* Timing information
* Errors and failures

The protocol allows implementations in different programming languages to produce compatible execution data.

```text
┌──────────────────────┐
│   Customer Runtime   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Language SDK / App  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Execution Protocol   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Platform / Consumers │
└──────────────────────┘
```

---

## Reference Runtime

`examples/reference_runtime` contains a demonstration customer application.

It consumes the SentinelAI SDK and optionally integrates with the Platform persistence/API packages.

The reference runtime is **not included in the installable SDK wheel**.

### Setup

Copy the environment configuration:

```bash
cp .env.example .env
```

Install development dependencies:

```bash
uv sync --extra reference --extra dev
```

Run database migrations:

```bash
uv run alembic upgrade head
```

Start the reference application:

```bash
uv run uvicorn examples.reference_runtime.main:app --reload
```

---

## Seed Sample Data

Once the reference server is running, sample documents can be created using:

```bash
uv run python examples/reference_runtime/scripts/seed_sample_documents.py
```

---

## Running the Application

### Canonical command

```bash
uv run uvicorn examples.reference_runtime.main:app --reload
```

### Deprecated compatibility launcher

The following launcher is retained temporarily for compatibility:

```bash
uv run uvicorn app.main:app --reload
```

Use the `examples.reference_runtime` entry point for new development.

---

## Database Migrations

SentinelAI supports database migrations through Alembic.

### Reference Deployment

The repository's reference deployment uses:

```text
alembic.ini
    │
    ▼
examples/reference_runtime/db/migrations
```

The reference migration environment registers demo document models while using the shared Platform revision chain.

### Platform-only Installation

For Platform-only deployments, Alembic can be configured to use:

```text
sentinelai_platform/persistence/postgres/migrations
```

### Migration Guidelines

Do not rewrite already-applied migration revisions.

For migration stamping and upgrade procedures, see:

```text
docs/architecture.md
```

---

## Development

Install all development dependencies:

```bash
uv sync --extra reference --extra dev
```

### Linting

```bash
uv run ruff check .
```

### Type Checking

```bash
uv run mypy
```

### Tests

```bash
uv run pytest
```

### Database Migration

```bash
uv run alembic upgrade head
```

### Migration Validation

```bash
uv run alembic check
```

### Run All Checks

```bash
uv run ruff check .
uv run mypy
uv run pytest
uv run alembic upgrade head
uv run alembic check
```

---

## Design Principles

SentinelAI follows a few core architectural principles.

### 1. SDK First

The SDK should remain useful without requiring the Platform.

```text
SDK
 │
 ├── Contracts
 ├── Execution
 ├── Tracing
 └── Event Publishing
```

### 2. Platform Is Optional

Persistence, APIs, storage, and analytics are Platform concerns.

```text
Core SDK
    │
    │ optional
    ▼
Platform
```

### 3. Protocol Is Language Neutral

Execution data should not be coupled to Python-specific implementation details.

### 4. Customer Logic Remains Customer-Owned

Applications should only need to annotate meaningful execution boundaries.

```python
@execution("query")
async def main(...):
    ...

@span("retrieval")
async def retrieve(...):
    ...

@span("generation")
async def generate(...):
    ...
```

The SDK handles the observability mechanics around those boundaries.

---

## Roadmap

The following namespaces are reserved for future Platform capabilities:

```text
sentinelai_platform.replay
sentinelai_platform.evaluation
sentinelai_platform.analytics
sentinelai_platform.dashboard
```

These capabilities are not currently implemented.

---

## Documentation

Detailed documentation is available in:

```text
docs/
├── architecture.md
└── public-api.md

protocol/
└── README.md
```

---

## Contributing

Contributions are welcome.

Before submitting a pull request, make sure the following checks pass:

```bash
uv run ruff check .
uv run mypy
uv run pytest
uv run alembic check
```

Please keep changes consistent with the existing SDK/Platform separation and avoid introducing Platform-specific dependencies into the core SDK.

---

## License

See the repository license for details.

