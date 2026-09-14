"""Step 5 unit tests for src/nrc_lexicon.py, written before running it on real review
text. Uses a small hand-built test lexicon, not the full downloaded EmoLex file, so these
tests do not depend on the (gitignored, separately downloaded) lexicon being present.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nrc_lexicon import EMOTIONS, primary_emotion, score_text_emotions, tokenize

# A small, hand-built lexicon for testing, independent of the real downloaded file.
TEST_LEXICON = {
    "happy": {"joy"},
    "furious": {"anger"},
    "scared": {"fear"},
    "surprised": {"surprise"},
    # A word deliberately tied between two emotions, to test the tie-break rule.
    "tense": {"fear", "anticipation"},
    # "calm" is intentionally absent from the lexicon (a word with no entry).
}


class TestTokenize(unittest.TestCase):
    def test_lowercases_and_splits_on_punctuation(self):
        self.assertEqual(tokenize("Happy, HAPPY!! day."), ["happy", "happy", "day"])

    def test_empty_text(self):
        self.assertEqual(tokenize(""), [])

    def test_none_text(self):
        self.assertEqual(tokenize(None), [])


class TestScoreTextEmotions(unittest.TestCase):
    def test_known_word_maps_to_specific_emotion(self):
        scores = score_text_emotions("I am so happy today", TEST_LEXICON)
        self.assertEqual(scores["joy"], 1)
        self.assertEqual(scores["anger"], 0)

    def test_word_with_no_lexicon_entry_contributes_nothing(self):
        scores = score_text_emotions("I feel calm and quiet", TEST_LEXICON)
        self.assertEqual(sum(scores.values()), 0)

    def test_multiple_occurrences_accumulate(self):
        scores = score_text_emotions("happy happy happy", TEST_LEXICON)
        self.assertEqual(scores["joy"], 3)

    def test_all_eight_emotions_present_in_output(self):
        scores = score_text_emotions("", TEST_LEXICON)
        self.assertEqual(set(scores.keys()), set(EMOTIONS))


class TestPrimaryEmotion(unittest.TestCase):
    def test_known_word_gives_correct_primary_emotion(self):
        emotion, scores = primary_emotion("I am furious about this", TEST_LEXICON)
        self.assertEqual(emotion, "anger")

    def test_word_with_no_entry_gives_none(self):
        emotion, scores = primary_emotion("calm quiet peaceful", TEST_LEXICON)
        self.assertIsNone(emotion)
        self.assertEqual(sum(scores.values()), 0)

    def test_empty_text_gives_none(self):
        emotion, scores = primary_emotion("", TEST_LEXICON)
        self.assertIsNone(emotion)

    def test_tie_broken_by_alphabetical_order(self):
        # "tense" scores fear and anticipation equally (1 each). EMOTIONS is alphabetical
        # order: anger, anticipation, disgust, fear, joy, sadness, surprise, trust.
        # anticipation comes before fear alphabetically, so it must win the tie.
        emotion, scores = primary_emotion("tense", TEST_LEXICON)
        self.assertEqual(scores["fear"], 1)
        self.assertEqual(scores["anticipation"], 1)
        self.assertEqual(emotion, "anticipation")

    def test_clear_winner_beats_tied_lower_scores(self):
        # "furious" contributes to anger only; "tense" contributes to fear and
        # anticipation. anger should still win outright since it has more matches.
        emotion, scores = primary_emotion("furious furious tense", TEST_LEXICON)
        self.assertEqual(scores["anger"], 2)
        self.assertEqual(emotion, "anger")


if __name__ == "__main__":
    unittest.main()
