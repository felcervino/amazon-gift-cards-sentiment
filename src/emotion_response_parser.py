"""Step 5: strict parser for the model's sentiment+emotion classification response.

Same design philosophy as src/response_parser.py (Step 1): anything that doesn't match
exactly (truncated, extra text, wrong casing, extra/missing keys, wrong value) is flagged
malformed, never silently coerced.
"""
import json
from dataclasses import dataclass
from typing import Optional

ALLOWED_LABELS = ("POSITIVE", "NEGATIVE")
ALLOWED_EMOTIONS = ("anger", "anticipation", "disgust", "fear", "joy", "sadness", "surprise", "trust")


@dataclass
class EmotionParseResult:
    status: str  # "ok" or "malformed"
    label: Optional[str]
    emotion: Optional[str]
    raw: str
    error: Optional[str]


def parse_emotion_response(raw: str) -> EmotionParseResult:
    stripped = raw.strip() if raw is not None else ""

    try:
        obj = json.loads(stripped)
    except json.JSONDecodeError as e:
        return EmotionParseResult("malformed", None, None, raw, f"invalid JSON: {e}")

    if not isinstance(obj, dict):
        return EmotionParseResult("malformed", None, None, raw, "response is not a JSON object")

    if set(obj.keys()) != {"label", "emotion"}:
        return EmotionParseResult(
            "malformed", None, None, raw,
            f"expected exactly the keys 'label' and 'emotion', got keys: {sorted(obj.keys())}",
        )

    label = obj["label"]
    if label not in ALLOWED_LABELS:
        return EmotionParseResult(
            "malformed", None, None, raw, f"label value {label!r} is not one of {ALLOWED_LABELS}",
        )

    emotion = obj["emotion"]
    if emotion not in ALLOWED_EMOTIONS:
        return EmotionParseResult(
            "malformed", None, None, raw, f"emotion value {emotion!r} is not one of {ALLOWED_EMOTIONS}",
        )

    return EmotionParseResult("ok", label, emotion, raw, None)
