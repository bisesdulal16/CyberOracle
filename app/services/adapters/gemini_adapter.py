# app/services/adapters/gemini_adapter.py

import os
from typing import Any, Dict

from app.services.adapters.base import BaseModelAdapter


class GeminiAdapter(BaseModelAdapter):
    """Adapter for Google Gemini models using the google-genai SDK."""

    def __init__(self):
        self._api_key = os.getenv("GOOGLE_API_KEY", "")

    async def generate(self, prompt: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from google import genai
        except ImportError:
            raise RuntimeError(
                "google-genai package is not installed. Run: pip install google-genai"
            )

        model_name = metadata.get("model_name", "gemini:gemini-2.0-flash")
        model_tag = (
            model_name.split("gemini:", 1)[1]
            if model_name.startswith("gemini:")
            else model_name
        )

        client = genai.Client(api_key=self._api_key)
        response = await client.aio.models.generate_content(
            model=model_tag,
            contents=prompt,
        )
        answer = response.text or ""

        return {"answer": answer, "model_used": model_name}
