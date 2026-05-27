"""Governance header parsing — the differentiator."""

from __future__ import annotations

from monago_atrium.governance import GovernanceMetadata


def test_full_headers_parsed():
    headers = {
        "X-Monago-Audit-Id": "audit-abc-123",
        "X-Monago-Pii-Detected": "true",
        "X-Monago-Pii-Redacted": "NIK, EMAIL, PHONE",
        "X-Monago-Policy-Decision": "allowed",
        "X-Monago-Provider": "openai",
        "X-Monago-Latency-Ms": "412.3",
        "X-Monago-Cost-Idr": "12.5",
    }
    g = GovernanceMetadata.from_headers(headers)
    assert g.audit_id == "audit-abc-123"
    assert g.pii_detected is True
    assert g.pii_redacted == ["NIK", "EMAIL", "PHONE"]
    assert g.policy_decision == "allowed"
    assert g.provider == "openai"
    assert g.latency_ms == 412.3
    assert g.cost_idr == 12.5
    assert g.blocked is False


def test_missing_headers_safe_defaults():
    g = GovernanceMetadata.from_headers({})
    assert g.audit_id is None
    assert g.pii_detected is False
    assert g.pii_redacted == []
    assert g.policy_decision is None
    assert g.provider is None
    assert g.latency_ms is None
    assert g.cost_idr is None
    assert g.security_incidents == []
    assert g.block_reason is None
    assert g.blocked is False


def test_partial_headers():
    headers = {"X-Monago-Audit-Id": "x", "X-Monago-Pii-Detected": "false"}
    g = GovernanceMetadata.from_headers(headers)
    assert g.audit_id == "x"
    assert g.pii_detected is False
    assert g.latency_ms is None


def test_malformed_numeric_does_not_crash():
    headers = {"X-Monago-Latency-Ms": "not-a-float", "X-Monago-Cost-Idr": ""}
    g = GovernanceMetadata.from_headers(headers)
    assert g.latency_ms is None
    assert g.cost_idr is None


def test_blocked_decision():
    headers = {
        "X-Monago-Policy-Decision": "blocked",
        "X-Monago-Block-Reason": "PII detected: NIK",
        "X-Monago-Audit-Id": "audit-blk-1",
    }
    g = GovernanceMetadata.from_headers(headers)
    assert g.blocked is True
    assert g.block_reason == "PII detected: NIK"
    assert g.audit_id == "audit-blk-1"


def test_bool_variants():
    for truthy in ("true", "True", "TRUE", "1", "yes", "y", "t"):
        g = GovernanceMetadata.from_headers({"X-Monago-Pii-Detected": truthy})
        assert g.pii_detected is True, f"failed for {truthy!r}"
    for falsy in ("false", "0", "no", "", "  "):
        g = GovernanceMetadata.from_headers({"X-Monago-Pii-Detected": falsy})
        assert g.pii_detected is False, f"failed for {falsy!r}"


def test_security_incidents_list():
    headers = {"X-Monago-Security-Incident": "prompt_injection, jailbreak_attempt"}
    g = GovernanceMetadata.from_headers(headers)
    assert g.security_incidents == ["prompt_injection", "jailbreak_attempt"]


def test_pii_redacted_handles_empty_segments():
    headers = {"X-Monago-Pii-Redacted": "NIK,,EMAIL, ,"}
    g = GovernanceMetadata.from_headers(headers)
    assert g.pii_redacted == ["NIK", "EMAIL"]
