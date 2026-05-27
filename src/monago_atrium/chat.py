"""Chat completions resource (sync + async).

Mirrors OpenAI's `client.chat.completions.create(...)` shape so existing
OpenAI-SDK code ports over by changing the import and base URL.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Mapping

import httpx

from .exceptions import (
    APIError,
    AtriumError,
    AuthError,
    ModelNotAllowedError,
    PIIBlockedError,
    PolicyBlockedError,
    RateLimitError,
    SecurityBlockedError,
    TimeoutError as AtriumTimeoutError,
)
from .governance import GovernanceMetadata
from .types import ChatCompletion, ChatMessage

if TYPE_CHECKING:
    from .client import AsyncAtrium, Atrium


MessageInput = Mapping[str, Any] | ChatMessage


def _normalize_messages(messages: Iterable[MessageInput]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in messages:
        if isinstance(m, ChatMessage):
            out.append(m.to_dict())
        elif isinstance(m, Mapping):
            out.append(dict(m))
        else:  # pragma: no cover - guarded by type hints
            raise TypeError(f"messages entries must be dict or ChatMessage, got {type(m)!r}")
    return out


def _build_body(
    *,
    model: str,
    messages: Iterable[MessageInput],
    temperature: float | None,
    max_tokens: int | None,
    top_p: float | None,
    stop: str | list[str] | None,
    extra: Mapping[str, Any] | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model,
        "messages": _normalize_messages(messages),
    }
    if temperature is not None:
        body["temperature"] = temperature
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
    if top_p is not None:
        body["top_p"] = top_p
    if stop is not None:
        body["stop"] = stop
    if extra:
        # Only OpenAI-compatible fields are accepted by the gateway
        # (extra="forbid"). `extra` is an escape hatch for future fields
        # the gateway adds before this SDK ships an update.
        for k, v in extra.items():
            body[k] = v
    return body


def _raise_for_status(response: httpx.Response) -> None:
    """Map HTTP errors to typed Atrium exceptions with governance context."""
    if response.status_code < 400:
        return

    governance = GovernanceMetadata.from_headers(response.headers)
    try:
        body = response.json() if response.content else None
    except ValueError:
        body = response.text

    message = "request failed"
    err_code: str | None = None
    if isinstance(body, dict):
        err_obj = body.get("error") if isinstance(body.get("error"), dict) else None
        if err_obj:
            message = str(err_obj.get("message") or message)
            err_code = err_obj.get("code") or err_obj.get("type")
        else:
            message = str(body.get("message") or message)
            err_code = body.get("code") or body.get("type")

    kwargs: dict[str, Any] = {
        "status_code": response.status_code,
        "audit_id": governance.audit_id,
        "block_reason": governance.block_reason,
        "policy_decision": governance.policy_decision,
        "response_body": body,
    }

    if response.status_code in (401, 403):
        raise AuthError(message or "unauthorized", **kwargs)
    if response.status_code == 429:
        raise RateLimitError(message or "rate limited", **kwargs)

    # 4xx policy/PII/security blocks
    if response.status_code in (400, 422, 451):
        code_lower = (err_code or "").lower()
        reason_lower = (governance.block_reason or "").lower()
        signal = f"{code_lower} {reason_lower}"
        if "pii" in signal:
            raise PIIBlockedError(message, **kwargs)
        if "security" in signal or "injection" in signal or "jailbreak" in signal:
            raise SecurityBlockedError(message, **kwargs)
        if "model" in signal and ("allow" in signal or "denied" in signal):
            raise ModelNotAllowedError(message, **kwargs)
        if governance.policy_decision == "blocked" or "policy" in signal:
            raise PolicyBlockedError(message, **kwargs)

    if response.status_code >= 500:
        raise APIError(message or "gateway error", **kwargs)

    raise AtriumError(message, **kwargs)


class Completions:
    """Sync chat.completions resource."""

    def __init__(self, client: "Atrium") -> None:
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: Iterable[MessageInput],
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        stop: str | list[str] | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> ChatCompletion:
        body = _build_body(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stop=stop,
            extra=extra,
        )
        try:
            response = self._client._http.post("/chat/completions", json=body)
        except httpx.TimeoutException as exc:
            raise AtriumTimeoutError(f"request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise APIError(f"network error: {exc}") from exc

        _raise_for_status(response)

        try:
            data = response.json()
        except ValueError as exc:
            raise APIError(f"invalid JSON response: {exc}") from exc

        governance = GovernanceMetadata.from_headers(response.headers)
        return ChatCompletion.from_response(data, governance)


class Chat:
    """Sync chat namespace (mirrors OpenAI SDK shape)."""

    def __init__(self, client: "Atrium") -> None:
        self.completions = Completions(client)


class AsyncCompletions:
    """Async chat.completions resource."""

    def __init__(self, client: "AsyncAtrium") -> None:
        self._client = client

    async def create(
        self,
        *,
        model: str,
        messages: Iterable[MessageInput],
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        stop: str | list[str] | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> ChatCompletion:
        body = _build_body(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stop=stop,
            extra=extra,
        )
        try:
            response = await self._client._http.post("/chat/completions", json=body)
        except httpx.TimeoutException as exc:
            raise AtriumTimeoutError(f"request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise APIError(f"network error: {exc}") from exc

        _raise_for_status(response)

        try:
            data = response.json()
        except ValueError as exc:
            raise APIError(f"invalid JSON response: {exc}") from exc

        governance = GovernanceMetadata.from_headers(response.headers)
        return ChatCompletion.from_response(data, governance)


class AsyncChat:
    """Async chat namespace."""

    def __init__(self, client: "AsyncAtrium") -> None:
        self.completions = AsyncCompletions(client)
