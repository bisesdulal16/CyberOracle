# app/services/model_router.py

from typing import Any, Dict, List

from app.services.adapters.ollama import OllamaAdapter

_ollama = OllamaAdapter(timeout_s=30)

# Supported model prefix registry — extend here when adding OpenAI etc.
SUPPORTED_PREFIXES = ("ollama:",)


def _assert_supported(model_name: str) -> None:
    if not model_name:
        raise ValueError("Model name is required.")
    if not any(model_name.lower().startswith(p) for p in SUPPORTED_PREFIXES):
        raise ValueError(
            f"Unsupported model '{model_name}'. "
            f"Supported prefixes: {SUPPORTED_PREFIXES}"
        )


async def route_one(
    prompt: str,
    model_requested: str,
    user_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Route a single prompt to the appropriate model adapter.

    Returns a dict with 'answer' and 'model_used'.
    """
    _assert_supported(model_requested)

    metadata = {
        "user_id": user_payload.get("user_id") or user_payload.get("id"),
        "model_name": model_requested,
    }

    return await _ollama.generate(prompt, metadata)


async def route_many(
    prompt: str,
    models: List[str],
    user_payload: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Route the same prompt to multiple models sequentially.
    Returns a list of results in the same order as `models`.
    """
    if not models:
        raise ValueError("'models' must contain at least 1 model.")

    results: List[Dict[str, Any]] = []
    for model in models:
        results.append(await route_one(prompt, model, user_payload))

    return results
