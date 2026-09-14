"""Step 1 unit tests for src/response_parser.py, written before running it on real data.

Covers expected-good responses and expected-malformed responses (truncated, extra text,
wrong casing, wrong/extra keys), per PLAN.md Section 6.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from response_parser import parse_response


class TestGoodResponses(unittest.TestCase):
    def test_positive(self):
        result = parse_response('{"label": "POSITIVE"}')
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "POSITIVE")
        self.assertIsNone(result.error)

    def test_negative(self):
        result = parse_response('{"label": "NEGATIVE"}')
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "NEGATIVE")

    def test_surrounding_whitespace_and_newline_tolerated(self):
        result = parse_response('  \n{"label": "POSITIVE"}\n  ')
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "POSITIVE")


class TestMalformedResponses(unittest.TestCase):
    def test_truncated_json(self):
        result = parse_response('{"label": "POSI')
        self.assertEqual(result.status, "malformed")
        self.assertIsNone(result.label)
        self.assertIn("invalid JSON", result.error)

    def test_extra_text_before(self):
        result = parse_response('Sure, here is the answer: {"label": "POSITIVE"}')
        self.assertEqual(result.status, "malformed")
        self.assertIsNone(result.label)

    def test_extra_text_after(self):
        result = parse_response('{"label": "NEGATIVE"} Hope that helps!')
        self.assertEqual(result.status, "malformed")
        self.assertIsNone(result.label)

    def test_wrong_casing_lowercase(self):
        result = parse_response('{"label": "positive"}')
        self.assertEqual(result.status, "malformed")
        self.assertIsNone(result.label)

    def test_wrong_casing_titlecase(self):
        result = parse_response('{"label": "Negative"}')
        self.assertEqual(result.status, "malformed")

    def test_extra_key(self):
        result = parse_response('{"label": "POSITIVE", "confidence": 0.9}')
        self.assertEqual(result.status, "malformed")

    def test_wrong_key_name(self):
        result = parse_response('{"sentiment": "POSITIVE"}')
        self.assertEqual(result.status, "malformed")

    def test_bare_word_not_json(self):
        result = parse_response("POSITIVE")
        self.assertEqual(result.status, "malformed")

    def test_empty_string(self):
        result = parse_response("")
        self.assertEqual(result.status, "malformed")

    def test_unexpected_label_value(self):
        result = parse_response('{"label": "NEUTRAL"}')
        self.assertEqual(result.status, "malformed")

    def test_json_array_not_object(self):
        result = parse_response('["POSITIVE"]')
        self.assertEqual(result.status, "malformed")

    def test_wrong_value_type(self):
        result = parse_response('{"label": 1}')
        self.assertEqual(result.status, "malformed")

    def test_markdown_code_fence_wrapped(self):
        result = parse_response('```json\n{"label": "POSITIVE"}\n```')
        self.assertEqual(result.status, "malformed")

    def test_none_input(self):
        result = parse_response(None)
        self.assertEqual(result.status, "malformed")


if __name__ == "__main__":
    unittest.main()
