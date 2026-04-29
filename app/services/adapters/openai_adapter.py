# app/services/adapters/openai_adapter.py

import os
from typing import Any, Dict

from app.services.adapters.base import BaseModelAdapter


class OpenAIAdapter(BaseModelAdapter):
    """Adapter for OpenAI-hosted models (gpt-4o, gpt-4o-mini, etc.)."""

    def __init__(self):
        self._api_key = os.getenv("OPENAI_API_KEY", "")

    async def generate(self, prompt: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise RuntimeError(
                "openai package is not installed. Run: pip install openai>=1.0.0"
            )

        model_name = metadata.get("model_name", "openai:gpt-4o-mini")
        model_tag = (
            model_name.split("openai:", 1)[1]
            if model_name.startswith("openai:")
            else model_name
        )

        client = AsyncOpenAI(api_key=self._api_key)
        response = await client.chat.completions.create(
            model=model_tag,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.choices[0].message.content or ""

        return {"answer": answer, "model_used": model_name}
