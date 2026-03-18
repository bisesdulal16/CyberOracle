import pytest
import httpx

from app.services.ollama_client import OllamaClient


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", "http://test/api/chat")
            response = httpx.Response(
                self.status_code,
                request=request,
                text=self.text,
            )
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=request,
                response=response,
            )

    def json(self):
        if isinstance(self._json, Exception):
            raise self._json
        return self._json


class DummyAsyncClientMessage:
    def __init__(self, *args, **kwargs):
        self.closed = False

    async def post(self, url, json=None):
        return DummyResponse(
            status_code=200,
            json_data={"message": {"role": "assistant", "content": "hi from mock"}},
        )

    async def aclose(self):
        self.closed = True


class DummyAsyncClientFallbackResponse:
    def __init__(self, *args, **kwargs):
        self.closed = False

    async def post(self, url, json=None):
        return DummyResponse(
            status_code=200,
            json_data={"response": "fallback response"},
        )

    async def aclose(self):
        self.closed = True


class DummyAsyncClientNonJSON:
    def __init__(self, *args, **kwargs):
        self.closed = False

    async def post(self, url, json=None):
        return DummyResponse(
            status_code=200,
            json_data=ValueError("bad json"),
            text="not-json-body",
        )

    async def aclose(self):
        self.closed = True


class DummyAsyncClientUnexpectedFormat:
    def __init__(self, *args, **kwargs):
        self.closed = False

    async def post(self, url, json=None):
        return DummyResponse(
            status_code=200,
            json_data={"message": {"role": "assistant"}},
        )

    async def aclose(self):
        self.closed = True


class DummyAsyncClientHTTPError:
    def __init__(self, *args, **kwargs):
        self.closed = False

    async def post(self, url, json=None):
        return DummyResponse(
            status_code=500,
            json_data={"error": "server exploded"},
            text="server exploded",
        )

    async def aclose(self):
        self.closed = True


class DummyAsyncClientRequestError:
    def __init__(self, *args, **kwargs):
        self.closed = False

    async def post(self, url, json=None):
        raise httpx.RequestError(
            "network issue",
            request=httpx.Request("POST", url),
        )

    async def aclose(self):
        self.closed = True


class DummyAsyncClientTimeoutThenSuccess:
    def __init__(self, *args, **kwargs):
        self.calls = 0
        self.closed = False

    async def post(self, url, json=None):
        self.calls += 1
        if self.calls == 1:
            raise httpx.ReadTimeout(
                "timeout",
                request=httpx.Request("POST", url),
            )
        return DummyResponse(
            status_code=200,
            json_data={"message": {"role": "assistant", "content": "retry success"}},
        )

    async def aclose(self):
        self.closed = True


class DummyAsyncClientAlwaysTimeout:
    def __init__(self, *args, **kwargs):
        self.closed = False

    async def post(self, url, json=None):
        raise httpx.ConnectError(
            "cannot connect",
            request=httpx.Request("POST", url),
        )

    async def aclose(self):
        self.closed = True


@pytest.fixture(autouse=True)
async def reset_shared_client():
    OllamaClient._shared_client = None
    yield
    await OllamaClient.aclose_shared_client()
    OllamaClient._shared_client = None


@pytest.mark.asyncio
async def test_get_client_reuses_shared_instance(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClientMessage)

    client = OllamaClient(base_url="http://localhost:11434", timeout=10.0)

    c1 = await client._get_client()
    c2 = await client._get_client()

    assert c1 is c2


@pytest.mark.asyncio
async def test_ollama_generate_parses_message_content(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClientMessage)

    client = OllamaClient(base_url="http://localhost:11434", timeout=10.0)
    out = await client.generate("llama3:latest", "hi")

    assert out == "hi from mock"


@pytest.mark.asyncio
async def test_ollama_generate_falls_back_to_response_field(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClientFallbackResponse)

    client = OllamaClient(base_url="http://localhost:11434", timeout=10.0)
    out = await client.generate("llama3:latest", "hi")

    assert out == "fallback response"


@pytest.mark.asyncio
async def test_ollama_generate_non_json_response_raises_runtime_error(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClientNonJSON)

    client = OllamaClient(base_url="http://localhost:11434", timeout=10.0)

    with pytest.raises(RuntimeError, match="non-JSON response"):
        await client.generate("llama3:latest", "hi")


@pytest.mark.asyncio
async def test_ollama_generate_unexpected_format_raises_runtime_error(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClientUnexpectedFormat)

    client = OllamaClient(base_url="http://localhost:11434", timeout=10.0)

    with pytest.raises(RuntimeError, match="Unexpected Ollama response format"):
        await client.generate("llama3:latest", "hi")


@pytest.mark.asyncio
async def test_ollama_generate_retries_after_timeout(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClientTimeoutThenSuccess)

    async def _no_sleep(_seconds):
        return None

    monkeypatch.setattr("app.services.ollama_client.asyncio.sleep", _no_sleep)

    client = OllamaClient(base_url="http://localhost:11434", timeout=10.0, retries=1)
    out = await client.generate("llama3:latest", "hi")

    assert out == "retry success"


@pytest.mark.asyncio
async def test_ollama_generate_timeout_after_retries_raises_runtime_error(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClientAlwaysTimeout)

    async def _no_sleep(_seconds):
        return None

    monkeypatch.setattr("app.services.ollama_client.asyncio.sleep", _no_sleep)

    client = OllamaClient(base_url="http://localhost:11434", timeout=10.0, retries=1)

    with pytest.raises(RuntimeError, match="timed out/connection error"):
        await client.generate("llama3:latest", "hi")


@pytest.mark.asyncio
async def test_ollama_generate_http_status_error_raises_runtime_error(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClientHTTPError)

    client = OllamaClient(base_url="http://localhost:11434", timeout=10.0)

    with pytest.raises(RuntimeError, match="Ollama HTTP error 500"):
        await client.generate("llama3:latest", "hi")


@pytest.mark.asyncio
async def test_ollama_generate_request_error_raises_runtime_error(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClientRequestError)

    client = OllamaClient(base_url="http://localhost:11434", timeout=10.0)

    with pytest.raises(RuntimeError, match="Ollama request error"):
        await client.generate("llama3:latest", "hi")


@pytest.mark.asyncio
async def test_aclose_shared_client_resets_shared_client(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClientMessage)

    client = OllamaClient(base_url="http://localhost:11434", timeout=10.0)
    shared = await client._get_client()

    assert OllamaClient._shared_client is shared

    await OllamaClient.aclose_shared_client()

    assert OllamaClient._shared_client is None
    assert shared.closed is True
