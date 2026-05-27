# Changelog

All notable changes to the Atrium SDK (Python) are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-05-27

Initial release. The headline value: **governance is visible** on every response.

### Added

- `Atrium` and `AsyncAtrium` clients with OpenAI-compatible base URL handling.
- `chat.completions.create(model=..., messages=..., ...)` — sync and async.
- `GovernanceMetadata` dataclass parsed from `X-Monago-*` response headers:
  - `audit_id`, `pii_detected`, `pii_redacted`, `policy_decision`,
    `provider`, `latency_ms`, `cost_idr`, `security_incidents`, `block_reason`.
  - Robust to missing or malformed headers — safe defaults, never crashes.
- Typed exception hierarchy. Block errors carry governance metadata so the
  audit trail survives the error path:
  - `AtriumError` → `AuthError`, `RateLimitError`, `APIError`, `TimeoutError`,
    `PolicyBlockedError` → `PIIBlockedError`, `SecurityBlockedError`, `ModelNotAllowedError`.
- Full type hints, `py.typed` marker.
- API key resolution from `api_key=` arg or `ATRIUM_API_KEY` / `MONAGO_API_KEY` env vars.
