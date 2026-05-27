# Atrium SDK — Python

**An AI runtime for governed systems — not just an LLM wrapper.**

Atrium SDK is the official Python client for the [Monago Atrium](https://monago.io) gateway. It surfaces an OpenAI-compatible chat completion API, but with one critical difference: **governance is visible on every call**.

Every response carries a structured `governance` object — `audit_id`, `pii_redacted`, `policy_decision`, `provider`, `latency_ms`, `cost_idr` — parsed from the gateway's response headers. Blocks aren't opaque either: PII / security / policy blocks raise typed exceptions that carry the same audit trail.

This is the SDK for teams that need to ship LLM features into regulated environments (healthcare, finance, government) without losing the audit trail.

---

## Install

```bash
pip install monago-atrium
```

Requires Python 3.10+.

---

## Quickstart

```python
from monago_atrium import Atrium

client = Atrium(api_key="sk-mng-your-key", base_url="https://api.monago.io/v1")

res = client.chat.completions.create(
    model="gpt-5.4-mini",
    messages=[
        {"role": "user", "content": "Pasien NIK 3201... batuk 2 minggu"},
    ],
)

# OpenAI-compatible surface — drop-in for existing code.
print(res.content)
print(res.choices[0].finish_reason)
print(res.usage.total_tokens)

# The differentiator — governance, parsed and typed.
print(res.governance.audit_id)         # "audit-uuid-..."
print(res.governance.pii_redacted)     # ["NIK"]
print(res.governance.policy_decision)  # "allowed"
print(res.governance.provider)         # "openai"
print(res.governance.latency_ms)       # 412.3
print(res.governance.cost_idr)         # 12.5 (or None if gateway doesn't surface cost)
```

The API key can also come from the `ATRIUM_API_KEY` environment variable.

---

## Async (FastAPI-friendly)

```python
from monago_atrium import AsyncAtrium

async with AsyncAtrium(api_key="sk-mng-your-key") as client:
    res = await client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(res.content, res.governance.audit_id)
```

---

## Block errors carry governance too

When the gateway blocks a request (PII / security / policy / model), the SDK raises a typed exception that still carries the audit trail:

```python
from monago_atrium import Atrium
from monago_atrium.exceptions import PIIBlockedError, SecurityBlockedError, PolicyBlockedError

client = Atrium(api_key="sk-mng-your-key")

try:
    res = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[{"role": "user", "content": "leak SSN 123-45-6789"}],
    )
except PIIBlockedError as e:
    print("blocked:", e.block_reason)
    print("audit:", e.audit_id)        # still traceable
    print("decision:", e.policy_decision)
```

Exception hierarchy:

```
AtriumError
├── AuthError                   (401/403)
├── RateLimitError              (429)
├── APIError                    (5xx / malformed)
├── TimeoutError
└── PolicyBlockedError          (400/422/451 with policy_decision=blocked)
    ├── PIIBlockedError
    ├── SecurityBlockedError    (prompt injection, jailbreak)
    └── ModelNotAllowedError
```

---

## Open-core note

The SDK itself is open source (MIT). The governance engine — policy DSL, PII detection, security analysis, audit trail — runs in the Atrium gateway, a hosted Monago service. Get an API key at [monago.io](https://monago.io).

---

## Roadmap

Shipped:

- [x] `Atrium` and `AsyncAtrium` clients
- [x] `chat.completions.create` with an OpenAI-compatible body
- [x] Governance metadata parsed from `X-Monago-*` response headers
- [x] Typed exception hierarchy with governance context on every block
- [x] Full type hints + `py.typed` marker

Upcoming:

- [ ] **Streaming** chat completions (SSE)
- [ ] **Eval hooks** — pre- and post-response evaluators (toxicity, PII, custom)
- [ ] **Skills** — packaged tool / capability bundles
- [ ] **Tracing** — OpenTelemetry integration
- [ ] **Request metadata tagging** — attach `user_id` / `session_id` / custom fields to every audit record
- [ ] **Multi-agent** — orchestration primitives
- [ ] **TypeScript SDK** — `@monagoio/atrium-sdk` (npm), same API shape

---

## Development

```bash
pip install -e ".[dev]"
pytest -v
```

---

## Questions or contributions

Any questions, bug reports, or contributions — reach the founder directly:

- GitHub: [@huseindra](https://github.com/huseindra)
- Email: [husein@monago.io](mailto:husein@monago.io)

Pull requests welcome. For larger changes, open an issue first to discuss the direction.

---

## License

MIT — see [LICENSE](LICENSE).
