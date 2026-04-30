# app/services/adapters/groq_adapter.py

import os
from typing import Any, Dict

from app.services.adapters.base import BaseModelAdapter

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqAdapter(BaseModelAdapter):
    """Adapter for Groq-hosted models (llama-3.3-70b, mixtral-8x7b, etc.).

    Groq exposes an OpenAI-compatible API, so we reuse the openai SDK
    pointed at Groq's base URL.
    """

    def __init__(self):
        self._api_key = os.getenv("GROQ_API_KEY", "")

    async def generate(self, prompt: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise RuntimeError(
                "openai package is not installed. Run: pip install openai>=1.0.0"
            )

        model_name = metadata.get("model_name", "groq:llama-3.3-70b-versatile")
        model_tag = (
            model_name.split("groq:", 1)[1]
            if model_name.startswith("groq:")
            else model_name
        )

        client = AsyncOpenAI(api_key=self._api_key, base_url=GROQ_BASE_URL)
        response = await client.chat.completions.create(
            model=model_tag,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.choices[0].message.content or ""

        return {"answer": answer, "model_used": model_name}
