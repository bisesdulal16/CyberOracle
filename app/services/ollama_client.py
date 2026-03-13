# app/services/ollama_client.py
from __future__ import annotations

import os
import asyncio
from typing import Optional

import httpx


class OllamaClient:
    """
    Ollama client (stable for production-ish use).

    Key fixes:
    - Uses /api/chat (works with modern Ollama)
    - Reuses a shared AsyncClient (connection pooling + fewer random hangs)
    - Configurable timeout + retries (reduces 502 ReadTimeout)
    - Better error messages returned to FastAPI (so your 502 shows the real cause)

    Environment variables:
    - OLLAMA_BASE_URL   (default: http://localhost:11434)
    - OLLAMA_TIMEOUT    (default: 300 seconds)
    - OLLAMA_RETRIES    (default: 2)
    """

    _shared_client: Optional[httpx.AsyncClient] = None
    _client_lock = asyncio.Lock()

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        retries: int | None = None,
    ):
        self.base_url = (
            base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ).rstrip("/")

        # Read timeout is what matters most for generation
        env_timeout = os.getenv("OLLAMA_TIMEOUT")
        self.read_timeout = float(
            timeout if timeout is not None else (env_timeout if env_timeout else 300.0)
        )

        env_retries = os.getenv("OLLAMA_RETRIES")
        self.retries = int(
            retries if retries is not None else (env_retries if env_retries else 2)
        )

        # Timeouts: generous read, normal connect/write
        self._timeout = httpx.Timeout(
            connect=10.0, read=self.read_timeout, write=30.0, pool=30.0
        )

        # Pool limits: keep enough connections alive
        self._limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)

    async def _get_client(self) -> httpx.AsyncClient:
        """
        Get or create a shared httpx AsyncClient so we reuse connections.
        This avoids creating a new TCP connection per message (which can cause hangs/timeouts).
        """
        if self.__class__._shared_client is not None:
            return self.__class__._shared_client

        async with self.__class__._client_lock:
            if self.__class__._shared_client is None:
                self.__class__._shared_client = httpx.AsyncClient(
                    timeout=self._timeout,
                    limits=self._limits,
                    headers={"Content-Type": "application/json"},
                )
            return self.__class__._shared_client

    async def generate(self, model: str, prompt: str) -> str:
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        client = await self._get_client()

        last_err: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()

                # Defensive JSON parsing
                try:
                    data = resp.json()
                except Exception:
                    raise RuntimeError(
                        f"Ollama returned non-JSON response: {resp.text[:400]}"
                    )

                # Expected modern format
                msg = data.get("message") or {}
                content = msg.get("content")
                if isinstance(content, str):
                    return content

                # Fallback older format
                if isinstance(data.get("response"), str):
                    return data["response"]

                raise RuntimeError(f"Unexpected Ollama response format: {data}")

            except (httpx.ReadTimeout, httpx.ConnectError) as e:
                # retry with small backoff
                last_err = e
                if attempt < self.retries:
                    await asyncio.sleep(0.4 * (attempt + 1))
                    continue
                raise RuntimeError(
                    f"Ollama timed out/connection error at {url}. "
                    f"Try increasing OLLAMA_TIMEOUT (currently {self.read_timeout}s). "
                    f"Error: {repr(e)}"
                ) from e

            except httpx.HTTPStatusError as e:
                status = e.response.status_code if e.response else "unknown"
                body = e.response.text[:600] if e.response else ""
                raise RuntimeError(
                    f"Ollama HTTP error {status} at {url}. Body: {body}"
                ) from e

            except httpx.RequestError as e:
                raise RuntimeError(f"Ollama request error at {url}: {repr(e)}") from e

        # Should never hit here
        raise RuntimeError(f"Ollama failed after retries. Last error: {repr(last_err)}")

    @classmethod
    async def aclose_shared_client(cls) -> None:
        """
        Optional: call this on app shutdown if you want clean teardown.
        (Not required for dev.)
        """
        if cls._shared_client is not None:
            await cls._shared_client.aclose()
            cls._shared_client = None
