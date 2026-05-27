"""Atrium SDK exception hierarchy.

Block errors carry governance metadata (audit_id, block_reason, policy_decision),
so developers can trace *why* a request was blocked — block is never opaque.
"""

from __future__ import annotations

from typing import Any


class AtriumError(Exception):
    """Base exception for all Atrium SDK errors.

    Carries governance metadata when available, so even error paths
    surface audit_id and reasoning.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        audit_id: str | None = None,
        block_reason: str | None = None,
        policy_decision: str | None = None,
        response_body: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.audit_id = audit_id
        self.block_reason = block_reason
        self.policy_decision = policy_decision
        self.response_body = response_body

    def __repr__(self) -> str:
        parts = [f"message={self.message!r}"]
        if self.status_code is not None:
            parts.append(f"status_code={self.status_code}")
        if self.audit_id:
            parts.append(f"audit_id={self.audit_id!r}")
        if self.block_reason:
            parts.append(f"block_reason={self.block_reason!r}")
        return f"{type(self).__name__}({', '.join(parts)})"


class AuthError(AtriumError):
    """Raised when the API key is missing, invalid, or unauthorized (401/403)."""


class PolicyBlockedError(AtriumError):
    """Raised when the gateway's policy engine blocks the request."""


class PIIBlockedError(PolicyBlockedError):
    """Raised when PII was detected and policy blocked the request."""


class SecurityBlockedError(PolicyBlockedError):
    """Raised when a security incident (prompt injection, jailbreak) blocked the request."""


class ModelNotAllowedError(PolicyBlockedError):
    """Raised when the requested model is not permitted for this workspace/API key."""


class RateLimitError(AtriumError):
    """Raised when the gateway returns 429."""


class TimeoutError(AtriumError):  # noqa: A001 - intentionally shadows builtin
    """Raised when the request times out."""


class APIError(AtriumError):
    """Raised for unexpected gateway errors (5xx, malformed response)."""
