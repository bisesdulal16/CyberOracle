# app/services/model_router.py
from typing import Dict, Any, List

from app.services.adapters.ollama import OllamaAdapter

_ollama = OllamaAdapter(timeout_s=30)

# Week 1/2: only support ollama
SUPPORTED_PREFIXES = ("ollama:",)  # add "openai:" later


def _assert_supported(model_name: str) -> None:
    if not model_name:
        raise ValueError("Model is required.")
    if not any(model_name.lower().startswith(p) for p in SUPPORTED_PREFIXES):
        raise ValueError(f"Unsupported model: {model_name}")


async def route_one(prompt: str, model_requested: str, user_payload: dict) -> Dict[str, Any]:
    _assert_supported(model_requested)

    metadata = {
        "user_id": user_payload.get("user_id") or user_payload.get("id"),
        "model_name": model_requested,
    }

    # right now only ollama supported
    return await _ollama.generate(prompt, metadata)


async def route_many(prompt: str, models: List[str], user_payload: dict) -> List[Dict[str, Any]]:
    if not models:
        raise ValueError("'models' must contain at least 1 model.")

    # sequential execution (simple + predictable)
    results: List[Dict[str, Any]] = []
    for m in models:
        results.append(await route_one(prompt, m, user_payload))

    return results
