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

class AnthropicProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__(name="anthropic")
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1")

    async def generate(self, request: ChatCompletionRequest, model: str) -> ChatCompletionResponse:
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not configured on Gateway server")

        start_time = time.time()
        
        # Format messages for Anthropic
        system_prompt = ""
        user_messages = []
        for m in request.messages:
            if m.role == "system":
                system_prompt += m.content + "\n"
            else:
                user_messages.append({"role": m.role, "content": m.content})

        payload = {
            "model": model,
            "messages": user_messages,
            "max_tokens": request.max_tokens or 1000,
        }
        if system_prompt:
            payload["system"] = system_prompt.strip()

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if resp.status_code != 200:
                raise RuntimeError(f"Anthropic API error ({resp.status_code}): {resp.text}")

            data = resp.json()
            elapsed_ms = (time.time() - start_time) * 1000.0

            content_text = ""
            if "content" in data and isinstance(data["content"], list):
                content_text = "".join([c.get("text", "") for c in data["content"]])

            input_tokens = data.get("usage", {}).get("input_tokens", 0)
            output_tokens = data.get("usage", {}).get("output_tokens", 0)

            return ChatCompletionResponse(
                id=data.get("id", f"msg_{uuid.uuid4().hex[:12]}"),
                created=int(time.time()),
                model=model,
                provider_served="anthropic",
                choices=[
                    Choice(
                        index=0,
                        message=ChatMessage(role="assistant", content=content_text),
                        finish_reason="stop"
                    )
                ],
                usage=UsageInfo(
                    prompt_tokens=input_tokens,
                    completion_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens
                ),
                latency_ms=elapsed_ms
            )

    async def stream_generate(self, request: ChatCompletionRequest, model: str) -> AsyncGenerator[str, None]:
        # For simplicity in translation, delegate to non-streaming or convert SSE stream
        res = await self.generate(request, model)
        req_id = res.id
        chunk = {
            "id": req_id,
            "object": "chat.completion.chunk",
            "created": res.created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": res.choices[0].message.content},
                    "finish_reason": "stop"
                }
            ]
        }
        yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"
