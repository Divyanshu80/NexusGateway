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

class OllamaProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__(name="ollama")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api")

    async def generate(self, request: ChatCompletionRequest, model: str) -> ChatCompletionResponse:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat",
                json={
                    "model": model,
                    "messages": [m.model_dump() for m in request.messages],
                    "stream": False
                }
            )
            
            if resp.status_code != 200:
                raise RuntimeError(f"Ollama local service error ({resp.status_code}): {resp.text}")

            data = resp.json()
            elapsed_ms = (time.time() - start_time) * 1000.0

            msg_content = data.get("message", {}).get("content", "")
            eval_count = data.get("eval_count", 0)
            prompt_eval_count = data.get("prompt_eval_count", 0)

            return ChatCompletionResponse(
                id=f"ollama-{uuid.uuid4().hex[:12]}",
                created=int(time.time()),
                model=model,
                provider_served="ollama",
                choices=[
                    Choice(
                        index=0,
                        message=ChatMessage(role="assistant", content=msg_content),
                        finish_reason="stop"
                    )
                ],
                usage=UsageInfo(
                    prompt_tokens=prompt_eval_count,
                    completion_tokens=eval_count,
                    total_tokens=prompt_eval_count + eval_count
                ),
                latency_ms=elapsed_ms
            )

    async def stream_generate(self, request: ChatCompletionRequest, model: str) -> AsyncGenerator[str, None]:
        res = await self.generate(request, model)
        chunk = {
            "id": res.id,
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
