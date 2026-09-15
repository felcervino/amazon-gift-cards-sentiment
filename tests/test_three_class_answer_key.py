"""Step 6 unit tests for src/three_class_answer_key.py, written before running it on
real data. Extends test_answer_key.py's coverage for the new three-way boundary: the
critical case is that rating exactly 3.0 must land in NEUTRAL, not silently fall through
to NEGATIVE (Step 2's binary rule) or POSITIVE.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from three_class_answer_key import three_class_answer_key


class TestThreeClassAnswerKey(unittest.TestCase):
    def test_rating_5_is_positive(self):
        result = three_class_answer_key(5.0)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "POSITIVE")

    def test_rating_4_is_positive(self):
        result = three_class_answer_key(4.0)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "POSITIVE")

    def test_rating_3_is_neutral(self):
        # The critical case for this step: 3-star must be its own NEUTRAL class here,
        # unlike Step 2's binary stage where it was NEGATIVE.
        result = three_class_answer_key(3.0)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "NEUTRAL")

    def test_rating_2_is_negative(self):
        result = three_class_answer_key(2.0)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "NEGATIVE")

    def test_rating_1_is_negative(self):
        result = three_class_answer_key(1.0)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "NEGATIVE")

    def test_rating_none_flagged(self):
        result = three_class_answer_key(None)
        self.assertEqual(result.status, "flagged")

    def test_rating_string_flagged(self):
        result = three_class_answer_key("3")
        self.assertEqual(result.status, "flagged")

    def test_rating_zero_flagged(self):
        result = three_class_answer_key(0.0)
        self.assertEqual(result.status, "flagged")

    def test_rating_six_flagged(self):
        result = three_class_answer_key(6.0)
        self.assertEqual(result.status, "flagged")

    def test_rating_non_integral_flagged(self):
        result = three_class_answer_key(3.5)
        self.assertEqual(result.status, "flagged")

    def test_rating_bool_flagged(self):
        result = three_class_answer_key(True)
        self.assertEqual(result.status, "flagged")

    def test_binary_and_three_class_agree_on_positive_and_negative_extremes(self):
        # Sanity cross-check against Step 2's binary rule: both rules must still agree
        # that 5/4 are POSITIVE-side and 1/2 are NEGATIVE-side; the two rules only
        # genuinely diverge at rating 3.0.
        from answer_key import binary_answer_key
        for rating in (1.0, 2.0, 4.0, 5.0):
            binary = binary_answer_key(rating)
            three_class = three_class_answer_key(rating)
            same_side = (
                (binary.label == "POSITIVE" and three_class.label == "POSITIVE")
                or (binary.label == "NEGATIVE" and three_class.label == "NEGATIVE")
            )
            self.assertTrue(same_side, f"rating {rating}: binary={binary.label}, three_class={three_class.label}")

    def test_binary_and_three_class_diverge_at_rating_3(self):
        from answer_key import binary_answer_key
        binary = binary_answer_key(3.0)
        three_class = three_class_answer_key(3.0)
        self.assertEqual(binary.label, "NEGATIVE")
        self.assertEqual(three_class.label, "NEUTRAL")


if __name__ == "__main__":
    unittest.main()
