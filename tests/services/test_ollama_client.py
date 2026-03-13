# app/tests/services/test_ollama_client.py
import pytest
from app.services.ollama_client import OllamaClient


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("HTTP error")

    def json(self):
        return self._json


class DummyAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None):
        # Simulate Ollama /api/chat response format
        return DummyResponse(
            status_code=200,
            json_data={"message": {"role": "assistant", "content": "hi from mock"}},
        )


@pytest.mark.asyncio
async def test_ollama_generate_parses_message_content(monkeypatch):
    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClient)

    client = OllamaClient(base_url="http://localhost:11434", timeout=10.0)
    out = await client.generate("llama3:latest", "hi")
    assert out == "hi from mock"
