from typing import List
from fastapi import APIRouter
from pydantic import BaseModel
from app.schemas.gateway import ProviderHealthStatus
from app.services.health_checker import health_checker
from app.services.fallback_router import fallback_router
from app.providers.mock_provider import MockLLMProvider

router = APIRouter(prefix="/v1/resilience", tags=["Health & Circuit Breaker"])

class OutageToggleRequest(BaseModel):
    model: str
    active: bool = True

@router.get("/health", response_model=List[ProviderHealthStatus])
async def get_provider_health():
    return await health_checker.get_health_statuses()

@router.post("/outage-toggle")
async def toggle_simulated_outage(req: OutageToggleRequest):
    mock_provider = fallback_router.get_provider("mock")
    if isinstance(mock_provider, MockLLMProvider):
        mock_provider.set_outage(req.model, req.active)
        return {
            "status": "success",
            "model": req.model,
            "outage_active": req.active,
            "message": f"Simulated outage for '{req.model}' is now {'ACTIVE' if req.active else 'RESOLVED'}"
        }
    return {"status": "ignored"}
