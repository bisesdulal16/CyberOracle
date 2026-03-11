# app/services/adapters/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseModelAdapter(ABC):
    @abstractmethod
    async def generate(self, prompt: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {"answer": "", "model_used": ""}
