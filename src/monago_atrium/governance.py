"""GovernanceMetadata — the differentiator.

Parses Monago gateway governance headers (X-Monago-*) into a typed object
surfaced on every response (success AND error). Parsing is defensive:
missing headers yield safe defaults, never crashes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

# Header names emitted by the gateway (v0.45.0 governance surface).
# If gateway names diverge, update here.
HEADER_AUDIT_ID = "X-Monago-Audit-Id"
HEADER_PII_DETECTED = "X-Monago-Pii-Detected"
HEADER_PII_REDACTED = "X-Monago-Pii-Redacted"
HEADER_POLICY_DECISION = "X-Monago-Policy-Decision"
HEADER_PROVIDER = "X-Monago-Provider"
HEADER_LATENCY_MS = "X-Monago-Latency-Ms"
HEADER_COST_IDR = "X-Monago-Cost-Idr"
HEADER_SECURITY_INCIDENT = "X-Monago-Security-Incident"
HEADER_BLOCK_REASON = "X-Monago-Block-Reason"


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "t"}


def _parse_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_str(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    return value


@dataclass
class GovernanceMetadata:
    """Governance facts surfaced on every Atrium response.

    The whole point of the SDK: instead of opaque header strings,
    developers see structured fields — audit_id for tracing, pii_redacted
    to know what was stripped, policy_decision for compliance, cost_idr
    for chargeback.
    """

    audit_id: str | None = None
    pii_detected: bool = False
    pii_redacted: list[str] = field(default_factory=list)
    policy_decision: str | None = None
    provider: str | None = None
    latency_ms: float | None = None
    cost_idr: float | None = None
    security_incidents: list[str] = field(default_factory=list)
    block_reason: str | None = None

    @classmethod
    def from_headers(cls, headers: Mapping[str, str]) -> GovernanceMetadata:
        """Build a GovernanceMetadata from response headers.

        Httpx headers are case-insensitive Mappings; plain dicts work too if
        keys are already in the canonical X-Monago-* casing.
        """
        get = headers.get
        return cls(
            audit_id=_parse_str(get(HEADER_AUDIT_ID)),
            pii_detected=_parse_bool(get(HEADER_PII_DETECTED)),
            pii_redacted=_parse_list(get(HEADER_PII_REDACTED)),
            policy_decision=_parse_str(get(HEADER_POLICY_DECISION)),
            provider=_parse_str(get(HEADER_PROVIDER)),
            latency_ms=_parse_float(get(HEADER_LATENCY_MS)),
            cost_idr=_parse_float(get(HEADER_COST_IDR)),
            security_incidents=_parse_list(get(HEADER_SECURITY_INCIDENT)),
            block_reason=_parse_str(get(HEADER_BLOCK_REASON)),
        )

    @property
    def blocked(self) -> bool:
        return self.policy_decision == "blocked"
