import time
import asyncio
import uuid
import json
from typing import AsyncGenerator
from app.providers.base import BaseLLMProvider
from app.schemas.gateway import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Choice,
    ChatMessage,
    UsageInfo,
    ChoiceStream,
    ChoiceDelta
)

class MockLLMProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__(name="mock")
        self.simulated_outage_models = set()
        self.artificial_delay_ms = 80  # Default 80ms fast local response

    def set_outage(self, model: str, active: bool = True):
        if active:
            self.simulated_outage_models.add(model)
        else:
            self.simulated_outage_models.discard(model)

    async def generate(self, request: ChatCompletionRequest, model: str) -> ChatCompletionResponse:
        start_time = time.time()
        
        if model in self.simulated_outage_models:
            raise RuntimeError(f"Simulated Provider Outage for mock model '{model}'")

        await asyncio.sleep(self.artificial_delay_ms / 1000.0)

        prompt_text = " ".join([m.content for m in request.messages])
        prompt_tokens = max(10, len(prompt_text.split()))
        
        response_text = (
            f"[NexusGateway Mock Response from {model}] Processed request with "
            f"{len(request.messages)} message(s). All gateway policies, rate limits, "
            f"and budget checks verified successfully."
        )
        completion_tokens = max(20, len(response_text.split()))
        
        elapsed_ms = (time.time() - start_time) * 1000.0

        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            created=int(time.time()),
            model=model,
            provider_served="mock",
            choices=[
                Choice(
                    index=0,
                    message=ChatMessage(role="assistant", content=response_text),
                    finish_reason="stop"
                )
            ],
            usage=UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            ),
            latency_ms=elapsed_ms
        )

    async def stream_generate(self, request: ChatCompletionRequest, model: str) -> AsyncGenerator[str, None]:
        if model in self.simulated_outage_models:
            raise RuntimeError(f"Simulated Provider Outage for mock streaming model '{model}'")

        req_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created_time = int(time.time())

        chunks = [
            "[NexusGateway ", "Mock ", "Streaming ", "Response] ",
            "Serving model ", f"'{model}' ", "with real-time ", "SSE passthrough ", "active."
        ]

        for chunk_text in chunks:
            await asyncio.sleep(0.04) # 40ms stream interval
            data_payload = {
                "id": req_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": chunk_text},
                        "finish_reason": None
                    }
                ]
            }
            yield f"data: {json.dumps(data_payload)}\n\n"

        # Final chunk
        end_payload = {
            "id": req_id,
            "object": "chat.completion.chunk",
            "created": created_time,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }
            ]
        }
        yield f"data: {json.dumps(end_payload)}\n\n"
        yield "data: [DONE]\n\n"
