"""Step 2 unit tests for src/answer_key.py, written before running it on real data.

The critical case is rating 3.0: per the assignment's binary rule ("ge 4 positive, else
negative"), 3-star reviews are NEGATIVE at this stage, not excluded, not neutral, not
dropped. A prior draft of this plan had this backwards; these tests pin the correct
behavior down.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from answer_key import binary_answer_key


class TestBinaryAnswerKey(unittest.TestCase):
    def test_rating_5_is_positive(self):
        result = binary_answer_key(5.0)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "POSITIVE")

    def test_rating_4_is_positive(self):
        result = binary_answer_key(4.0)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "POSITIVE")

    def test_rating_3_is_negative(self):
        # The critical case: 3-star must be NEGATIVE, not excluded or neutral, at this stage.
        result = binary_answer_key(3.0)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "NEGATIVE")

    def test_rating_2_is_negative(self):
        result = binary_answer_key(2.0)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "NEGATIVE")

    def test_rating_1_is_negative(self):
        result = binary_answer_key(1.0)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "NEGATIVE")

    def test_rating_none_flagged(self):
        result = binary_answer_key(None)
        self.assertEqual(result.status, "flagged")
        self.assertIsNone(result.label)

    def test_rating_string_flagged(self):
        result = binary_answer_key("5")
        self.assertEqual(result.status, "flagged")
        self.assertIsNone(result.label)

    def test_rating_zero_flagged(self):
        result = binary_answer_key(0.0)
        self.assertEqual(result.status, "flagged")

    def test_rating_six_flagged(self):
        result = binary_answer_key(6.0)
        self.assertEqual(result.status, "flagged")

    def test_rating_non_integral_flagged(self):
        result = binary_answer_key(3.5)
        self.assertEqual(result.status, "flagged")

    def test_rating_bool_flagged(self):
        # bool is a subclass of int in Python; must not silently pass as a valid rating.
        result = binary_answer_key(True)
        self.assertEqual(result.status, "flagged")

    def test_rating_negative_number_flagged(self):
        result = binary_answer_key(-1.0)
        self.assertEqual(result.status, "flagged")


if __name__ == "__main__":
    unittest.main()
