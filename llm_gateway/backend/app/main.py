from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from app.core.config import settings
from app.api.router import api_router
from app.services.telemetry import telemetry

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="NexusGateway — Production LLM Gateway with Rate Limiting, Fallback Routing, and Unified Observability."
)

# Enable CORS for Next.js frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/", tags=["General"])
async def root():
    return {
        "name": settings.app_name,
        "version": settings.version,
        "status": "online",
        "proxy_endpoint": "/v1/chat/completions",
        "docs_url": "/docs"
    }

@app.get("/health", tags=["General"])
async def health_check():
    return {"status": "healthy"}

# Standard Prometheus scraping root endpoint
@app.get("/metrics", response_class=PlainTextResponse, tags=["Observability"])
async def prometheus_metrics():
    return telemetry.get_prometheus_metrics()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
