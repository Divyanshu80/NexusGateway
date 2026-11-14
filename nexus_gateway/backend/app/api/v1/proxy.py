import time
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from app.core.config import TeamConfig
from app.core.security import get_current_team
from app.schemas.gateway import ChatCompletionRequest, ChatCompletionResponse
from app.services.rate_limiter import rate_limiter
from app.services.budget_tracker import budget_tracker
from app.services.fallback_router import fallback_router
from app.services.telemetry import telemetry

router = APIRouter(prefix="/v1", tags=["OpenAI Proxy"])

@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    team: TeamConfig = Depends(get_current_team)
):
    start_time = time.time()
    
    # 1. Enforce Rate Limiting (Token Bucket RPM & TPM)
    allowed, rate_reason, retry_after = await rate_limiter.check_rate_limit(team, request.max_tokens or 100)
    if not allowed:
        telemetry.record_request(
            team_id=team.id,
            requested_model=request.model,
            served_model="none",
            provider_served="none",
            status_code=429,
            latency_ms=(time.time() - start_time) * 1000.0,
            prompt_tokens=0,
            completion_tokens=0,
            cost_usd=0.0,
            fallback_triggered=False
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=rate_reason,
            headers={"Retry-After": str(int(retry_after))}
        )

    # 2. Enforce Budget Caps (USD Monthly limit)
    budget_allowed, warning_triggered, budget_msg = budget_tracker.check_budget(team)
    if not budget_allowed:
        telemetry.record_request(
            team_id=team.id,
            requested_model=request.model,
            served_model="none",
            provider_served="none",
            status_code=402,
            latency_ms=(time.time() - start_time) * 1000.0,
            prompt_tokens=0,
            completion_tokens=0,
            cost_usd=0.0,
            fallback_triggered=False
        )
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=budget_msg
        )

    # 3. Apply System Prompt Injection / Policy Disclaimer if configured
    if team.system_prompt_override:
        has_system = any(m.role == "system" for m in request.messages)
        if not has_system:
            request.messages.insert(0, {"role": "system", "content": team.system_prompt_override})

    # 4. Handle Streaming SSE vs Standard JSON Response
    if request.stream:
        stream_gen, provider_used, model_used = await fallback_router.execute_stream_with_fallback(request, team.id)
        return StreamingResponse(
            stream_gen,
            media_type="text/event-stream",
            headers={
                "X-Gateway-Provider": provider_used,
                "X-Gateway-Model-Served": model_used,
                "X-Gateway-Team": team.id
            }
        )

    # 5. Non-streaming Execution via Fallback Router Engine
    try:
        response, fallback_triggered = await fallback_router.execute_with_fallback(request, team.id)
        
        telemetry.record_request(
            team_id=team.id,
            requested_model=request.model,
            served_model=response.model,
            provider_served=response.provider_served,
            status_code=200,
            latency_ms=response.latency_ms,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            cost_usd=response.cost_usd,
            fallback_triggered=fallback_triggered
        )

        return response
    except Exception as e:
        telemetry.record_request(
            team_id=team.id,
            requested_model=request.model,
            served_model="none",
            provider_served="none",
            status_code=500,
            latency_ms=(time.time() - start_time) * 1000.0,
            prompt_tokens=0,
            completion_tokens=0,
            cost_usd=0.0,
            fallback_triggered=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"NexusGateway Routing Exception: {str(e)}"
        )
