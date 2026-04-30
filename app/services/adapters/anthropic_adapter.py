# app/services/adapters/anthropic_adapter.py

import os
from typing import Any, Dict

from app.services.adapters.base import BaseModelAdapter


class AnthropicAdapter(BaseModelAdapter):
    """Adapter for Anthropic Claude models (claude-3-5-haiku, claude-3-5-sonnet, etc.)."""

    def __init__(self):
        self._api_key = os.getenv("ANTHROPIC_API_KEY", "")

    async def generate(self, prompt: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import anthropic
        except ImportError:
            raise RuntimeError(
                "anthropic package is not installed. Run: pip install anthropic>=0.20.0"
            )

        model_name = metadata.get("model_name", "anthropic:claude-3-5-haiku-20241022")
        model_tag = (
            model_name.split("anthropic:", 1)[1]
            if model_name.startswith("anthropic:")
            else model_name
        )

        client = anthropic.AsyncAnthropic(api_key=self._api_key)
        message = await client.messages.create(
            model=model_tag,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = message.content[0].text if message.content else ""

        return {"answer": answer, "model_used": model_name}
