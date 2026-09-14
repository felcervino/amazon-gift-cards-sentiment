"""Step 3 unit tests for src/generate_dashboard.py, including regression tests for the two
bugs found by the Red Team pass: non-finite ratings breaking the embedded JSON, and
unpaired UTF-16 surrogates crashing the file write.
"""
import json
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from generate_dashboard import render_dashboard, safe_json_for_script, sanitize_records_for_embedding


class TestSanitizeRecords(unittest.TestCase):
    def test_finite_rating_passed_through(self):
        records = [{"review_id": 1, "rating": 4.0}]
        cleaned = sanitize_records_for_embedding(records)
        self.assertEqual(cleaned[0]["rating"], 4.0)

    def test_nan_rating_nulled(self):
        records = [{"review_id": 1, "rating": float("nan")}]
        cleaned = sanitize_records_for_embedding(records)
        self.assertIsNone(cleaned[0]["rating"])

    def test_infinity_rating_nulled(self):
        records = [{"review_id": 1, "rating": float("inf")}]
        cleaned = sanitize_records_for_embedding(records)
        self.assertIsNone(cleaned[0]["rating"])

    def test_negative_infinity_rating_nulled(self):
        records = [{"review_id": 1, "rating": float("-inf")}]
        cleaned = sanitize_records_for_embedding(records)
        self.assertIsNone(cleaned[0]["rating"])

    def test_other_fields_untouched(self):
        records = [{"review_id": 1, "rating": 5.0, "title": "Great", "match": True}]
        cleaned = sanitize_records_for_embedding(records)
        self.assertEqual(cleaned[0]["title"], "Great")
        self.assertEqual(cleaned[0]["match"], True)


class TestNanRatingProducesValidJson(unittest.TestCase):
    def test_render_dashboard_with_nan_rating_is_valid_json(self):
        # Regression test for the Red Team finding: a NaN rating used to produce the
        # literal (invalid JSON) token NaN in the embedded script block, which would
        # throw on JSON.parse in the browser and break the whole page.
        adversarial_record = {
            "review_id": 1,
            "title": "corrupted row",
            "text": "some text",
            "rating": float("nan"),
            "answer_key_status": "flagged",
            "answer_key_label": None,
            "answer_key_error": "rating is not a number",
            "raw_model_response": '{"label": "POSITIVE"}',
            "parsed_status": "ok",
            "parsed_label": "POSITIVE",
            "parsed_error": None,
            "match": None,
        }
        html = render_dashboard([adversarial_record])

        start_marker = '<script id="review-data" type="application/json">'
        end_marker = "</script>"
        start = html.index(start_marker) + len(start_marker)
        end = html.index(end_marker, start)
        embedded_json_text = html[start:end]

        # This must not raise: the embedded text must be valid JSON, not the literal
        # NaN token.
        parsed = json.loads(embedded_json_text)
        self.assertIsNone(parsed[0]["rating"])
        self.assertNotIn("NaN", embedded_json_text)
        self.assertNotIn("Infinity", embedded_json_text)


class TestSurrogateWriteDoesNotCrash(unittest.TestCase):
    def test_unpaired_surrogate_write_does_not_raise(self):
        # Regression test for the Red Team finding: an unpaired UTF-16 surrogate in
        # title/text used to raise UnicodeEncodeError on the strict utf-8 file write,
        # crashing dashboard generation outright.
        adversarial_record = {
            "review_id": 1,
            "title": "bad surrogate: \ud800 end",
            "text": "text",
            "rating": 5.0,
            "answer_key_status": "ok",
            "answer_key_label": "POSITIVE",
            "answer_key_error": None,
            "raw_model_response": '{"label": "POSITIVE"}',
            "parsed_status": "ok",
            "parsed_label": "POSITIVE",
            "parsed_error": None,
            "match": True,
        }
        html = render_dashboard([adversarial_record])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_output.html")
            # Must not raise UnicodeEncodeError.
            with open(path, "w", encoding="utf-8", errors="replace") as f:
                f.write(html)
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 0)


if __name__ == "__main__":
    unittest.main()
