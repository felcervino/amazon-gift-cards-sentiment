"""Step 2: binary answer key derived from the star rating only.

Rule (from the assignment, confirmed in PLAN.md Section 7): rating >= 4 is POSITIVE, else
NEGATIVE. Every rating below 4, including 3-star reviews, is NEGATIVE at this stage. A true
NEUTRAL class does not exist until Step 6. Unexpected rating values are flagged, never
silently coerced.
"""
from dataclasses import dataclass
from typing import Optional

EXPECTED_RATINGS = (1.0, 2.0, 3.0, 4.0, 5.0)


@dataclass
class AnswerKeyResult:
    status: str  # "ok" or "flagged"
    label: Optional[str]
    rating: object
    error: Optional[str]


def binary_answer_key(rating) -> AnswerKeyResult:
    if isinstance(rating, bool) or not isinstance(rating, (int, float)):
        return AnswerKeyResult("flagged", None, rating, f"rating is not a number: {rating!r}")

    rating_f = float(rating)
    if rating_f not in EXPECTED_RATINGS:
        return AnswerKeyResult(
            "flagged", None, rating, f"rating outside expected {{1,2,3,4,5}}: {rating!r}"
        )

    label = "POSITIVE" if rating_f >= 4.0 else "NEGATIVE"
    return AnswerKeyResult("ok", label, rating, None)
