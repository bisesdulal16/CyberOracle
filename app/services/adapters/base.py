# app/services/adapters/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseModelAdapter(ABC):
    """
    Abstract base for all model adapters.
    Each backend (Ollama, OpenAI, etc.) implements this interface.
    """

    @abstractmethod
    async def generate(self, prompt: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a response for the given prompt.

        Returns a dict with at minimum:
            answer    : str  — the model's text response
            model_used: str  — the model identifier that was used
        """
        raise NotImplementedError
