from abc import ABC, abstractmethod
from typing import AsyncGenerator
from app.schemas.gateway import ChatCompletionRequest, ChatCompletionResponse

class BaseLLMProvider(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def generate(self, request: ChatCompletionRequest, model: str) -> ChatCompletionResponse:
        """Non-streaming generation"""
        pass

    @abstractmethod
    async def stream_generate(self, request: ChatCompletionRequest, model: str) -> AsyncGenerator[str, None]:
        """Streaming SSE generation generator yielding chunks"""
        pass
