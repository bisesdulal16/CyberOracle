# app/services/adapters/ollama.py

from typing import Any, Dict

from app.services.adapters.base import BaseModelAdapter
from app.services.ollama_client import OllamaClient


class OllamaAdapter(BaseModelAdapter):
    """
    Concrete adapter that delegates to the shared OllamaClient.
    Translates the generic adapter interface into OllamaClient.generate() calls.
    """

    def __init__(self, timeout_s: int = 30):
        self.timeout_s = timeout_s
        self._client = OllamaClient()

    async def generate(self, prompt: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        model_name = metadata.get("model_name", "ollama:llama3")

        # Strip the "ollama:" prefix to get the raw Ollama model tag
        if model_name.startswith("ollama:"):
            model_tag = model_name.split("ollama:", 1)[1]
        else:
            model_tag = model_name

        answer = await self._client.generate(model_tag, prompt)

        return {
            "answer": answer,
            "model_used": model_name,
        }
