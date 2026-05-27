"""Minimal chat completion example.

Run with:
    export ATRIUM_API_KEY=mk_live_...
    python examples/basic_chat.py
"""

from __future__ import annotations

from monago_atrium import Atrium


def main() -> None:
    client = Atrium()  # picks up ATRIUM_API_KEY from env

    res = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[
            {"role": "system", "content": "Kamu asisten singkat dan ramah."},
            {"role": "user", "content": "Halo, apa kabar?"},
        ],
        temperature=0.7,
        max_tokens=150,
    )

    print("Response:", res.content)
    print("Model:", res.model)
    print("Tokens:", res.usage.total_tokens)


if __name__ == "__main__":
    main()
