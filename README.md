SentinelAI

SentinelAI is an AI observability platform with four independent products: the language-neutral Execution Protocol, the Python SDK, the optional Platform, and customer runtimes.

Install

# Core SDK (Pydantic only)
uv add sentinelai

# Optional Platform backend (API + persistence + storage)
uv add "sentinelai[platform]"

# This repository / reference runtime
uv sync --extra reference --extra dev
