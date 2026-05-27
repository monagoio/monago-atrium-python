"""Error path — block responses carry governance metadata."""

from __future__ import annotations

import httpx
import pytest

from monago_atrium import Atrium
from monago_atrium.exceptions import (
    APIError,
    AuthError,
    ModelNotAllowedError,
    PIIBlockedError,
    PolicyBlockedError,
    RateLimitError,
    SecurityBlockedError,
)


def _client_with_response(response: httpx.Response) -> Atrium:
    transport = httpx.MockTransport(lambda _req: response)
    http = httpx.Client(
        base_url="https://api.monago.io/v1",
        headers={"Authorization": "Bearer mk_test"},
        transport=transport,
    )
    return Atrium(api_key="mk_test", http_client=http)


def _call(client: Atrium):
    return client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[{"role": "user", "content": "hi"}],
    )


def test_pii_block_carries_audit_and_reason():
    response = httpx.Response(
        400,
        headers={
            "X-Monago-Audit-Id": "audit-blk-pii",
            "X-Monago-Policy-Decision": "blocked",
            "X-Monago-Block-Reason": "PII detected: NIK",
            "X-Monago-Pii-Detected": "true",
            "X-Monago-Pii-Redacted": "NIK",
        },
        json={"error": {"message": "PII detected and policy blocked", "code": "pii_blocked"}},
    )
    client = _client_with_response(response)
    with pytest.raises(PIIBlockedError) as exc_info:
        _call(client)
    err = exc_info.value
    assert err.audit_id == "audit-blk-pii"
    assert err.block_reason == "PII detected: NIK"
    assert err.policy_decision == "blocked"
    assert err.status_code == 400
    assert isinstance(err, PolicyBlockedError)


def test_security_block():
    response = httpx.Response(
        400,
        headers={
            "X-Monago-Audit-Id": "audit-blk-sec",
            "X-Monago-Policy-Decision": "blocked",
            "X-Monago-Block-Reason": "prompt injection detected",
            "X-Monago-Security-Incident": "prompt_injection",
        },
        json={"error": {"message": "security incident", "code": "security_block"}},
    )
    client = _client_with_response(response)
    with pytest.raises(SecurityBlockedError) as exc_info:
        _call(client)
    assert exc_info.value.audit_id == "audit-blk-sec"


def test_model_not_allowed():
    response = httpx.Response(
        400,
        headers={
            "X-Monago-Audit-Id": "audit-blk-mdl",
            "X-Monago-Policy-Decision": "blocked",
            "X-Monago-Block-Reason": "model not allowed for workspace",
        },
        json={"error": {"message": "model denied", "code": "model_not_allowed"}},
    )
    client = _client_with_response(response)
    with pytest.raises(ModelNotAllowedError):
        _call(client)


def test_generic_policy_block():
    response = httpx.Response(
        400,
        headers={
            "X-Monago-Audit-Id": "audit-blk-pol",
            "X-Monago-Policy-Decision": "blocked",
            "X-Monago-Block-Reason": "rule violation: r-42",
        },
        json={"error": {"message": "policy rule blocked", "code": "policy_blocked"}},
    )
    client = _client_with_response(response)
    with pytest.raises(PolicyBlockedError) as exc_info:
        _call(client)
    err = exc_info.value
    # Should not be a PII or security subclass
    assert not isinstance(err, PIIBlockedError)
    assert not isinstance(err, SecurityBlockedError)
    assert err.block_reason == "rule violation: r-42"


def test_auth_error_401():
    response = httpx.Response(
        401,
        json={"error": {"message": "invalid api key"}},
    )
    client = _client_with_response(response)
    with pytest.raises(AuthError) as exc_info:
        _call(client)
    assert exc_info.value.status_code == 401


def test_rate_limit_429():
    response = httpx.Response(
        429,
        json={"error": {"message": "too many requests"}},
    )
    client = _client_with_response(response)
    with pytest.raises(RateLimitError):
        _call(client)


def test_server_error_5xx():
    response = httpx.Response(503, text="upstream unavailable")
    client = _client_with_response(response)
    with pytest.raises(APIError) as exc_info:
        _call(client)
    assert exc_info.value.status_code == 503
