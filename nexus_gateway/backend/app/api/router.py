from fastapi import APIRouter
from app.api.v1 import proxy, teams, resilience, metrics

api_router = APIRouter()

api_router.include_router(proxy.router)
api_router.include_router(teams.router)
api_router.include_router(resilience.router)
api_router.include_router(metrics.router)
