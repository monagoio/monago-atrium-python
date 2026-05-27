"""Atrium and AsyncAtrium clients."""

from __future__ import annotations

import os
from typing import Any

import httpx

from .chat import AsyncChat, Chat
from .exceptions import AuthError

DEFAULT_BASE_URL = "https://api.monago.io/v1"
DEFAULT_TIMEOUT = 60.0
_SDK_VERSION = "0.1.0"
_USER_AGENT = f"monago-atrium-python/{_SDK_VERSION}"


def _resolve_api_key(api_key: str | None) -> str:
    key = api_key or os.environ.get("ATRIUM_API_KEY") or os.environ.get("MONAGO_API_KEY")
    if not key:
        raise AuthError(
            "missing API key — pass api_key= or set ATRIUM_API_KEY environment variable"
        )
    return key


def _headers(api_key: str, extra: dict[str, str] | None) -> dict[str, str]:
    h = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": _USER_AGENT,
    }
    if extra:
        h.update(extra)
    return h


class Atrium:
    """Synchronous Atrium client.

    Example:
        >>> from monago_atrium import Atrium
        >>> client = Atrium(api_key="sk-mng-...")
        >>> res = client.chat.completions.create(
        ...     model="gpt-5.4-mini",
        ...     messages=[{"role": "user", "content": "Hello"}],
        ... )
        >>> print(res.content)
        >>> print(res.governance.audit_id, res.governance.pii_redacted)
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        default_headers: dict[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.api_key = _resolve_api_key(api_key)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        if http_client is not None:
            self._http = http_client
            self._owns_http = False
        else:
            self._http = httpx.Client(
                base_url=self.base_url,
                headers=_headers(self.api_key, default_headers),
                timeout=timeout,
            )
            self._owns_http = True

        self.chat = Chat(self)

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> Atrium:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


class AsyncAtrium:
    """Asynchronous Atrium client (for FastAPI / asyncio apps).

    Example:
        >>> from monago_atrium import AsyncAtrium
        >>> async with AsyncAtrium(api_key="sk-mng-...") as client:
        ...     res = await client.chat.completions.create(
        ...         model="gpt-5.4-mini",
        ...         messages=[{"role": "user", "content": "Hello"}],
        ...     )
        ...     print(res.content)
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        default_headers: dict[str, str] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = _resolve_api_key(api_key)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        if http_client is not None:
            self._http = http_client
            self._owns_http = False
        else:
            self._http = httpx.AsyncClient(
                base_url=self.base_url,
                headers=_headers(self.api_key, default_headers),
                timeout=timeout,
            )
            self._owns_http = True

        self.chat = AsyncChat(self)

    async def close(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> AsyncAtrium:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()
