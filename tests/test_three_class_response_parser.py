"""Step 6 unit tests for src/three_class_response_parser.py, written before running it
on real data. Mirrors test_response_parser.py's coverage extended to the third NEUTRAL
label.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from three_class_response_parser import parse_three_class_response


class TestGoodResponses(unittest.TestCase):
    def test_positive(self):
        result = parse_three_class_response('{"label": "POSITIVE"}')
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "POSITIVE")

    def test_neutral(self):
        result = parse_three_class_response('{"label": "NEUTRAL"}')
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "NEUTRAL")

    def test_negative(self):
        result = parse_three_class_response('{"label": "NEGATIVE"}')
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "NEGATIVE")

    def test_surrounding_whitespace_tolerated(self):
        result = parse_three_class_response('  \n{"label": "NEUTRAL"}\n  ')
        self.assertEqual(result.status, "ok")


class TestMalformedResponses(unittest.TestCase):
    def test_truncated_json(self):
        result = parse_three_class_response('{"label": "NEU')
        self.assertEqual(result.status, "malformed")

    def test_extra_text_before(self):
        result = parse_three_class_response('Answer: {"label": "NEUTRAL"}')
        self.assertEqual(result.status, "malformed")

    def test_extra_text_after(self):
        result = parse_three_class_response('{"label": "NEUTRAL"} done')
        self.assertEqual(result.status, "malformed")

    def test_wrong_casing(self):
        result = parse_three_class_response('{"label": "neutral"}')
        self.assertEqual(result.status, "malformed")

    def test_extra_key(self):
        result = parse_three_class_response('{"label": "NEUTRAL", "confidence": 0.5}')
        self.assertEqual(result.status, "malformed")

    def test_wrong_key_name(self):
        result = parse_three_class_response('{"sentiment": "NEUTRAL"}')
        self.assertEqual(result.status, "malformed")

    def test_unexpected_label_value(self):
        # "MIXED" is not one of the three allowed labels.
        result = parse_three_class_response('{"label": "MIXED"}')
        self.assertEqual(result.status, "malformed")

    def test_bare_word_not_json(self):
        result = parse_three_class_response("NEUTRAL")
        self.assertEqual(result.status, "malformed")

    def test_empty_string(self):
        result = parse_three_class_response("")
        self.assertEqual(result.status, "malformed")

    def test_none_input(self):
        result = parse_three_class_response(None)
        self.assertEqual(result.status, "malformed")

    def test_json_array_not_object(self):
        result = parse_three_class_response('["NEUTRAL"]')
        self.assertEqual(result.status, "malformed")


if __name__ == "__main__":
    unittest.main()
