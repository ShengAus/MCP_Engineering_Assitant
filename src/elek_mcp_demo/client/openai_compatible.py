from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


DEFAULT_BASE_URL = "https://api.openai.com/v1"


@dataclass(frozen=True)
class LlmSettings:
    api_key: str
    model: str
    base_url: str = DEFAULT_BASE_URL

    @classmethod
    def from_env(cls) -> "LlmSettings":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required for the optional LLM host. "
                "The deterministic MCP demo does not require an API key."
            )

        return cls(
            api_key=api_key,
            model=os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4.1-mini",
            base_url=os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        )


class OpenAICompatibleChatClient:
    """Minimal OpenAI-compatible Chat Completions client for tool calling."""

    def __init__(self, settings: LlmSettings):
        self.settings = settings

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.settings.model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.settings.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            return response.json()
