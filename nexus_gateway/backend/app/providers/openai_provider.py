import os
import time
import uuid
import json
import httpx
from typing import AsyncGenerator
from app.providers.base import BaseLLMProvider
from app.schemas.gateway import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Choice,
    ChatMessage,
    UsageInfo
)

class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__(name="openai")
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    async def generate(self, request: ChatCompletionRequest, model: str) -> ChatCompletionResponse:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not configured on Gateway server")

        start_time = time.time()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [m.model_dump() for m in request.messages],
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "stream": False
                }
            )
            
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI API error ({resp.status_code}): {resp.text}")

            data = resp.json()
            elapsed_ms = (time.time() - start_time) * 1000.0

            return ChatCompletionResponse(
                id=data.get("id", f"chatcmpl-{uuid.uuid4().hex[:12]}"),
                created=data.get("created", int(time.time())),
                model=model,
                provider_served="openai",
                choices=[
                    Choice(
                        index=c.get("index", 0),
                        message=ChatMessage(
                            role=c["message"]["role"],
                            content=c["message"]["content"]
                        ),
                        finish_reason=c.get("finish_reason", "stop")
                    ) for c in data.get("choices", [])
                ],
                usage=UsageInfo(
                    prompt_tokens=data.get("usage", {}).get("prompt_tokens", 0),
                    completion_tokens=data.get("usage", {}).get("completion_tokens", 0),
                    total_tokens=data.get("usage", {}).get("total_tokens", 0)
                ),
                latency_ms=elapsed_ms
            )

    async def stream_generate(self, request: ChatCompletionRequest, model: str) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not configured on Gateway server")

        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [m.model_dump() for m in request.messages],
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "stream": True
                }
            ) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    raise RuntimeError(f"OpenAI Streaming error ({response.status_code}): {error_body.decode('utf-8')}")

                async for line in response.aiter_lines():
                    if line:
                        yield f"{line}\n\n"
