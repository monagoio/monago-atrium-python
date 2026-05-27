"""Governance visibility demo — the SDK's headline value.

Sends a prompt containing PII (Indonesian NIK) and shows what the gateway
reports back: PII detection, redaction list, policy decision, audit_id,
provider, latency, and cost.

Run with:
    export ATRIUM_API_KEY=mk_live_...
    python examples/governance_demo.py
"""

from __future__ import annotations

from monago_atrium import Atrium
from monago_atrium.exceptions import PIIBlockedError, PolicyBlockedError


def main() -> None:
    client = Atrium()

    pii_prompt = (
        "Pasien dengan NIK 3201234567890123 dan nomor HP 081234567890 datang "
        "dengan keluhan batuk sudah 2 minggu. Tolong analisis kemungkinan diagnosa."
    )

    try:
        res = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": "Kamu asisten klinis untuk dokter."},
                {"role": "user", "content": pii_prompt},
            ],
        )
    except PIIBlockedError as e:
        print("Request BLOCKED — PII policy")
        print(f"  audit_id:        {e.audit_id}")
        print(f"  block_reason:    {e.block_reason}")
        print(f"  policy_decision: {e.policy_decision}")
        return
    except PolicyBlockedError as e:
        print(f"Request BLOCKED — policy: {e.block_reason} (audit {e.audit_id})")
        return

    print("=" * 60)
    print("RESPONSE")
    print("=" * 60)
    print(res.content)

    print()
    print("=" * 60)
    print("GOVERNANCE — what the gateway tells us about this call")
    print("=" * 60)
    g = res.governance
    print(f"  audit_id:        {g.audit_id}")
    print(f"  provider:        {g.provider}")
    print(f"  policy_decision: {g.policy_decision}")
    print(f"  pii_detected:    {g.pii_detected}")
    print(f"  pii_redacted:    {g.pii_redacted}")
    print(f"  latency_ms:      {g.latency_ms}")
    print(f"  cost_idr:        {g.cost_idr}")
    if g.security_incidents:
        print(f"  security_incidents: {g.security_incidents}")


if __name__ == "__main__":
    main()
