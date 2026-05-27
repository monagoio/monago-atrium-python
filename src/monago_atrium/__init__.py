"""Atrium SDK — an AI runtime for governed systems.

Quickstart:

    from monago_atrium import Atrium

    client = Atrium(api_key="sk-mng-...")
    res = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(res.content)
    print(res.governance)  # audit_id, pii_redacted, policy_decision, ...
"""

from .client import AsyncAtrium, Atrium
from .exceptions import (
    APIError,
    AtriumError,
    AuthError,
    ModelNotAllowedError,
    PIIBlockedError,
    PolicyBlockedError,
    RateLimitError,
    SecurityBlockedError,
    TimeoutError,
)
from .governance import GovernanceMetadata
from .types import ChatCompletion, ChatMessage, Choice, Usage

__version__ = "0.1.0"

__all__ = [
    "Atrium",
    "AsyncAtrium",
    "GovernanceMetadata",
    "ChatCompletion",
    "ChatMessage",
    "Choice",
    "Usage",
    "AtriumError",
    "AuthError",
    "PolicyBlockedError",
    "PIIBlockedError",
    "SecurityBlockedError",
    "ModelNotAllowedError",
    "RateLimitError",
    "TimeoutError",
    "APIError",
    "__version__",
]
