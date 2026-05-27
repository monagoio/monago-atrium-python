"""Typed request and response models (OpenAI-compatible).

The gateway accepts OpenAI-compatible bodies (extra="forbid"), so requests
mirror OpenAI's shape exactly. Responses do too, plus a `.governance`
attribute attached by the SDK from response headers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .governance import GovernanceMetadata

Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class ChatMessage:
    """A single message in a chat completion request or response."""

    role: Role
    content: str
    name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.name is not None:
            d["name"] = self.name
        return d


@dataclass
class Usage:
    """Token usage stats from the provider (OpenAI-compatible)."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Usage:
        if not data:
            return cls()
        return cls(
            prompt_tokens=int(data.get("prompt_tokens", 0)),
            completion_tokens=int(data.get("completion_tokens", 0)),
            total_tokens=int(data.get("total_tokens", 0)),
        )


@dataclass
class Choice:
    """A single completion choice (OpenAI-compatible)."""

    index: int
    message: ChatMessage
    finish_reason: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Choice:
        msg_data = data.get("message") or {}
        return cls(
            index=int(data.get("index", 0)),
            message=ChatMessage(
                role=msg_data.get("role", "assistant"),
                content=msg_data.get("content") or "",
                name=msg_data.get("name"),
            ),
            finish_reason=data.get("finish_reason"),
        )


@dataclass
class ChatCompletion:
    """Result of a chat.completions.create call.

    OpenAI-compatible fields (id, model, choices, usage) plus the SDK's
    headline value: `governance`, parsed from gateway headers.
    """

    id: str
    model: str
    choices: list[Choice]
    usage: Usage
    governance: GovernanceMetadata
    created: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def content(self) -> str:
        """Shortcut for `choices[0].message.content` — the common case."""
        if not self.choices:
            return ""
        return self.choices[0].message.content

    @classmethod
    def from_response(
        cls,
        body: dict[str, Any],
        governance: GovernanceMetadata,
    ) -> ChatCompletion:
        return cls(
            id=str(body.get("id", "")),
            model=str(body.get("model", "")),
            choices=[Choice.from_dict(c) for c in body.get("choices", [])],
            usage=Usage.from_dict(body.get("usage")),
            governance=governance,
            created=body.get("created"),
            raw=body,
        )
