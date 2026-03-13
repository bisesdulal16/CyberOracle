import pytest

from app.services.model_router import route_many, route_one
from app.services.adapters.ollama import OllamaAdapter


@pytest.mark.asyncio
async def test_route_one_rejects_unsupported_model():
    with pytest.raises(ValueError, match="Unsupported model"):
        await route_one("hi", "openai:gpt-4o", {"user_id": "u1"})


@pytest.mark.asyncio
async def test_route_many_rejects_empty_models():
    with pytest.raises(ValueError, match="must contain at least 1 model"):
        await route_many("hi", [], {"user_id": "u1"})


@pytest.mark.asyncio
async def test_ollama_adapter_strips_prefix():
    captured = {}

    class FakeClient:
        async def generate(self, model: str, prompt: str) -> str:
            captured["model"] = model
            captured["prompt"] = prompt
            return "mocked response"

    adapter = OllamaAdapter()
    adapter._client = FakeClient()

    result = await adapter.generate(
        "hello",
        {"model_name": "ollama:llama3"},
    )

    assert captured["model"] == "llama3"
    assert captured["prompt"] == "hello"
    assert result["answer"] == "mocked response"
    assert result["model_used"] == "ollama:llama3"


@pytest.mark.asyncio
async def test_ollama_adapter_without_prefix():
    captured = {}

    class FakeClient:
        async def generate(self, model: str, prompt: str) -> str:
            captured["model"] = model
            captured["prompt"] = prompt
            return "plain model response"

    adapter = OllamaAdapter()
    adapter._client = FakeClient()

    result = await adapter.generate(
        "test prompt",
        {"model_name": "llama3"},
    )

    assert captured["model"] == "llama3"
    assert captured["prompt"] == "test prompt"
    assert result["answer"] == "plain model response"
    assert result["model_used"] == "llama3"