"""Step 6: three-class answer key derived from the star rating only.

Rule (PLAN.md Section 11, redefining Step 2's binary rule): 4-5 = POSITIVE, 3 = NEUTRAL,
1-2 = NEGATIVE. This is the point where 3-star reviews get their own genuine NEUTRAL
class, distinct from Step 2's binary stage where they were NEGATIVE. Unexpected rating
values are flagged, never silently coerced, same discipline as Step 2's binary_answer_key.
"""
from dataclasses import dataclass
from typing import Optional

EXPECTED_RATINGS = (1.0, 2.0, 3.0, 4.0, 5.0)


@dataclass
class ThreeClassAnswerKeyResult:
    status: str  # "ok" or "flagged"
    label: Optional[str]
    rating: object
    error: Optional[str]


def three_class_answer_key(rating) -> ThreeClassAnswerKeyResult:
    if isinstance(rating, bool) or not isinstance(rating, (int, float)):
        return ThreeClassAnswerKeyResult("flagged", None, rating, f"rating is not a number: {rating!r}")

    rating_f = float(rating)
    if rating_f not in EXPECTED_RATINGS:
        return ThreeClassAnswerKeyResult(
            "flagged", None, rating, f"rating outside expected {{1,2,3,4,5}}: {rating!r}"
        )

    if rating_f >= 4.0:
        label = "POSITIVE"
    elif rating_f == 3.0:
        label = "NEUTRAL"
    else:
        label = "NEGATIVE"

    return ThreeClassAnswerKeyResult("ok", label, rating, None)
