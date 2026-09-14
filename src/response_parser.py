"""Step 1: strict parser for the model's sentiment classification response.

Anything that doesn't match the expected format exactly (truncated JSON, extra text
before/after, wrong casing, extra/missing keys, wrong value) is flagged as malformed, never
silently coerced into a guess.
"""
import json
from dataclasses import dataclass
from typing import Optional

ALLOWED_LABELS = ("POSITIVE", "NEGATIVE")


@dataclass
class ParseResult:
    status: str  # "ok" or "malformed"
    label: Optional[str]
    raw: str
    error: Optional[str]


def parse_response(raw: str) -> ParseResult:
    stripped = raw.strip() if raw is not None else ""

    try:
        obj = json.loads(stripped)
    except json.JSONDecodeError as e:
        return ParseResult(status="malformed", label=None, raw=raw, error=f"invalid JSON: {e}")

    if not isinstance(obj, dict):
        return ParseResult(status="malformed", label=None, raw=raw, error="response is not a JSON object")

    if set(obj.keys()) != {"label"}:
        return ParseResult(
            status="malformed",
            label=None,
            raw=raw,
            error=f"expected exactly the key 'label', got keys: {sorted(obj.keys())}",
        )

    label = obj["label"]
    if label not in ALLOWED_LABELS:
        return ParseResult(
            status="malformed",
            label=None,
            raw=raw,
            error=f"label value {label!r} is not one of {ALLOWED_LABELS}",
        )

    return ParseResult(status="ok", label=label, raw=raw, error=None)
