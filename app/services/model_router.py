# app/services/model_router.py

from typing import Any, Dict, List

from app.services.adapters.ollama import OllamaAdapter
from app.services.adapters.openai_adapter import OpenAIAdapter
from app.services.adapters.anthropic_adapter import AnthropicAdapter
from app.services.adapters.gemini_adapter import GeminiAdapter
from app.services.adapters.groq_adapter import GroqAdapter

_ollama = OllamaAdapter(timeout_s=30)
_openai = OpenAIAdapter()
_anthropic = AnthropicAdapter()
_gemini = GeminiAdapter()
_groq = GroqAdapter()

SUPPORTED_PREFIXES = ("ollama:", "openai:", "anthropic:", "gemini:", "groq:")


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

    lower = model_requested.lower()
    if lower.startswith("openai:"):
        return await _openai.generate(prompt, metadata)
    elif lower.startswith("anthropic:"):
        return await _anthropic.generate(prompt, metadata)
    elif lower.startswith("gemini:"):
        return await _gemini.generate(prompt, metadata)
    elif lower.startswith("groq:"):
        return await _groq.generate(prompt, metadata)
    else:
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
