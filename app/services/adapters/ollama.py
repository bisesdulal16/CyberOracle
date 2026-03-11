# app/services/adapters/ollama.py
from typing import Dict, Any
from .base import BaseModelAdapter


class OllamaAdapter(BaseModelAdapter):
    def __init__(self, timeout_s: int = 30):
        self.timeout_s = timeout_s

    async def generate(self, prompt: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "answer": f"[ollama dummy] {prompt[:200]}",
            "model_used": metadata.get("model_name", "ollama:dummy"),
        }
