"""Chat completion happy-path with mocked httpx transport."""

from __future__ import annotations

import json

import httpx
import pytest

from monago_atrium import AsyncAtrium, Atrium, ChatMessage


def _success_response(request: httpx.Request) -> httpx.Response:
    # Assert outgoing request looks OpenAI-compatible
    body = json.loads(request.content.decode())
    assert body["model"] == "gpt-5.4-mini"
    assert body["messages"] == [{"role": "user", "content": "Pasien NIK 3201... batuk"}]
    assert request.headers["authorization"].startswith("Bearer ")

    headers = {
        "X-Monago-Audit-Id": "audit-success-1",
        "X-Monago-Pii-Detected": "true",
        "X-Monago-Pii-Redacted": "NIK",
        "X-Monago-Policy-Decision": "allowed",
        "X-Monago-Provider": "openai",
        "X-Monago-Latency-Ms": "350.0",
        "X-Monago-Cost-Idr": "8.75",
    }
    body_out = {
        "id": "cmpl-1",
        "model": "gpt-5.4-mini",
        "created": 1700000000,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Pasien dengan keluhan batuk..."},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 12, "completion_tokens": 18, "total_tokens": 30},
    }
    return httpx.Response(200, headers=headers, json=body_out)


def _make_sync_client() -> Atrium:
    transport = httpx.MockTransport(_success_response)
    http = httpx.Client(
        base_url="https://api.monago.io/v1",
        headers={"Authorization": "Bearer mk_test", "Content-Type": "application/json"},
        transport=transport,
    )
    return Atrium(api_key="mk_test", http_client=http)


def test_chat_completion_success_surfaces_content_and_governance():
    client = _make_sync_client()
    res = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[{"role": "user", "content": "Pasien NIK 3201... batuk"}],
    )

    # OpenAI-compatible surface
    assert res.id == "cmpl-1"
    assert res.model == "gpt-5.4-mini"
    assert res.content == "Pasien dengan keluhan batuk..."
    assert res.choices[0].finish_reason == "stop"
    assert res.usage.total_tokens == 30

    # Governance — the differentiator
    g = res.governance
    assert g.audit_id == "audit-success-1"
    assert g.pii_detected is True
    assert g.pii_redacted == ["NIK"]
    assert g.policy_decision == "allowed"
    assert g.provider == "openai"
    assert g.latency_ms == 350.0
    assert g.cost_idr == 8.75
    assert g.blocked is False


def test_chat_message_dataclass_accepted():
    client = _make_sync_client()
    res = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[ChatMessage(role="user", content="Pasien NIK 3201... batuk")],
    )
    assert res.content.startswith("Pasien")


@pytest.mark.asyncio
async def test_async_chat_completion():
    transport = httpx.MockTransport(_success_response)
    http = httpx.AsyncClient(
        base_url="https://api.monago.io/v1",
        headers={"Authorization": "Bearer mk_test", "Content-Type": "application/json"},
        transport=transport,
    )
    async with AsyncAtrium(api_key="mk_test", http_client=http) as client:
        res = await client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[{"role": "user", "content": "Pasien NIK 3201... batuk"}],
        )
    assert res.content.startswith("Pasien")
    assert res.governance.audit_id == "audit-success-1"


def test_missing_api_key_raises_auth_error(monkeypatch):
    monkeypatch.delenv("ATRIUM_API_KEY", raising=False)
    monkeypatch.delenv("MONAGO_API_KEY", raising=False)
    from monago_atrium.exceptions import AuthError

    with pytest.raises(AuthError):
        Atrium()


def test_api_key_from_env(monkeypatch):
    monkeypatch.setenv("ATRIUM_API_KEY", "mk_env_test")
    transport = httpx.MockTransport(_success_response)
    http = httpx.Client(
        base_url="https://api.monago.io/v1",
        headers={"Authorization": "Bearer mk_env_test", "Content-Type": "application/json"},
        transport=transport,
    )
    client = Atrium(http_client=http)
    assert client.api_key == "mk_env_test"
