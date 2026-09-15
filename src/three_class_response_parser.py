"""Step 6: strict parser for the three-class model response.

Same flag-don't-coerce design as src/response_parser.py (Step 1), extended to the
POSITIVE/NEUTRAL/NEGATIVE label set.
"""
import json
from dataclasses import dataclass
from typing import Optional

ALLOWED_LABELS = ("POSITIVE", "NEUTRAL", "NEGATIVE")


@dataclass
class ThreeClassParseResult:
    status: str  # "ok" or "malformed"
    label: Optional[str]
    raw: str
    error: Optional[str]


def parse_three_class_response(raw: str) -> ThreeClassParseResult:
    stripped = raw.strip() if raw is not None else ""

    try:
        obj = json.loads(stripped)
    except json.JSONDecodeError as e:
        return ThreeClassParseResult("malformed", None, raw, f"invalid JSON: {e}")

    if not isinstance(obj, dict):
        return ThreeClassParseResult("malformed", None, raw, "response is not a JSON object")

    if set(obj.keys()) != {"label"}:
        return ThreeClassParseResult(
            "malformed", None, raw, f"expected exactly the key 'label', got keys: {sorted(obj.keys())}",
        )

    label = obj["label"]
    if label not in ALLOWED_LABELS:
        return ThreeClassParseResult(
            "malformed", None, raw, f"label value {label!r} is not one of {ALLOWED_LABELS}",
        )

    return ThreeClassParseResult("ok", label, raw, None)
