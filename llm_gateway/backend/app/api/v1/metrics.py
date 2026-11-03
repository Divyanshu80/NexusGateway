from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from app.schemas.gateway import TelemetrySnapshot
from app.services.telemetry import telemetry

router = APIRouter(prefix="/v1/metrics", tags=["Metrics & Observability"])

@router.get("/summary", response_model=TelemetrySnapshot)
async def get_telemetry_summary():
    return telemetry.get_snapshot()

@router.get("/logs")
async def get_recent_request_logs():
    return telemetry.request_logs

@router.get("/prometheus", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    return telemetry.get_prometheus_metrics()
