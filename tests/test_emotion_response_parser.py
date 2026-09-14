"""Step 5 unit tests for src/emotion_response_parser.py, written before running it on
real data. Mirrors test_response_parser.py's coverage (good responses, malformed:
truncated, extra text, wrong casing, wrong/extra/missing keys) extended for the second
"emotion" key.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from emotion_response_parser import parse_emotion_response


class TestGoodResponses(unittest.TestCase):
    def test_positive_joy(self):
        result = parse_emotion_response('{"label": "POSITIVE", "emotion": "joy"}')
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "POSITIVE")
        self.assertEqual(result.emotion, "joy")

    def test_negative_anger(self):
        result = parse_emotion_response('{"label": "NEGATIVE", "emotion": "anger"}')
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.emotion, "anger")

    def test_all_eight_emotions_accepted(self):
        for emotion in ("anger", "anticipation", "disgust", "fear", "joy", "sadness", "surprise", "trust"):
            result = parse_emotion_response(f'{{"label": "POSITIVE", "emotion": "{emotion}"}}')
            self.assertEqual(result.status, "ok", f"emotion {emotion!r} should be accepted")

    def test_key_order_does_not_matter(self):
        result = parse_emotion_response('{"emotion": "trust", "label": "POSITIVE"}')
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.label, "POSITIVE")
        self.assertEqual(result.emotion, "trust")

    def test_surrounding_whitespace_tolerated(self):
        result = parse_emotion_response('  \n{"label": "NEGATIVE", "emotion": "sadness"}\n  ')
        self.assertEqual(result.status, "ok")


class TestMalformedResponses(unittest.TestCase):
    def test_truncated_json(self):
        result = parse_emotion_response('{"label": "POSITIVE", "emo')
        self.assertEqual(result.status, "malformed")

    def test_extra_text_before(self):
        result = parse_emotion_response('Here you go: {"label": "POSITIVE", "emotion": "joy"}')
        self.assertEqual(result.status, "malformed")

    def test_extra_text_after(self):
        result = parse_emotion_response('{"label": "POSITIVE", "emotion": "joy"} done!')
        self.assertEqual(result.status, "malformed")

    def test_wrong_casing_label(self):
        result = parse_emotion_response('{"label": "positive", "emotion": "joy"}')
        self.assertEqual(result.status, "malformed")

    def test_wrong_casing_emotion(self):
        result = parse_emotion_response('{"label": "POSITIVE", "emotion": "Joy"}')
        self.assertEqual(result.status, "malformed")

    def test_missing_emotion_key(self):
        result = parse_emotion_response('{"label": "POSITIVE"}')
        self.assertEqual(result.status, "malformed")

    def test_missing_label_key(self):
        result = parse_emotion_response('{"emotion": "joy"}')
        self.assertEqual(result.status, "malformed")

    def test_extra_key(self):
        result = parse_emotion_response('{"label": "POSITIVE", "emotion": "joy", "confidence": 0.9}')
        self.assertEqual(result.status, "malformed")

    def test_unexpected_emotion_value(self):
        # "neutral" and "love" are not among the 8 NRC categories.
        result = parse_emotion_response('{"label": "POSITIVE", "emotion": "love"}')
        self.assertEqual(result.status, "malformed")

    def test_unexpected_label_value(self):
        result = parse_emotion_response('{"label": "NEUTRAL", "emotion": "joy"}')
        self.assertEqual(result.status, "malformed")

    def test_bare_word_not_json(self):
        result = parse_emotion_response("joy")
        self.assertEqual(result.status, "malformed")

    def test_empty_string(self):
        result = parse_emotion_response("")
        self.assertEqual(result.status, "malformed")

    def test_none_input(self):
        result = parse_emotion_response(None)
        self.assertEqual(result.status, "malformed")


if __name__ == "__main__":
    unittest.main()
