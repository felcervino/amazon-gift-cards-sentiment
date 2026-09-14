"""Step 5: NRC Word-Emotion Association Lexicon (EmoLex) word-list emotion detection.

No model calls; runs over review text already saved from Step 1/2. Source: the NRC
Emotion Lexicon, Saif Mohammad and Peter Turney, National Research Council Canada,
http://saifmohammad.com/WebPages/NRC-Emotion-Lexicon.htm (free for non-commercial
research/educational use, citation required, redistribution of the data itself is not
permitted by its terms of use, so the lexicon file is gitignored, not committed, see
data/nrc_lexicon/NRC-Emotion-Lexicon/README.txt for the full terms).

Tie-break rule for primary_emotion(): when two or more of the 8 emotions are tied for the
highest score, the fixed alphabetical order below decides the winner. A text with zero
matching emotion words returns None (no primary emotion determinable), not a silent
default to any one emotion.
"""
import os
import re
from collections import defaultdict

LEXICON_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "nrc_lexicon", "NRC-Emotion-Lexicon",
    "NRC-Emotion-Lexicon-Wordlevel-v0.92.txt",
)

EMOTIONS = ("anger", "anticipation", "disgust", "fear", "joy", "sadness", "surprise", "trust")

_WORD_RE = re.compile(r"[a-zA-Z']+")


def load_lexicon(path=LEXICON_PATH):
    """Load the word-level lexicon into {word: set(emotions_present)}.

    Only the 8 emotion categories are kept; the lexicon's own "positive"/"negative"
    sentiment rows are excluded, since Step 5 asks for primary emotion, not sentiment
    (sentiment is already Step 1/2's job).
    """
    lexicon = defaultdict(set)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            word, emotion, association = line.split("\t")
            if emotion not in EMOTIONS:
                continue
            if association == "1":
                lexicon[word].add(emotion)
    return dict(lexicon)


def tokenize(text: str):
    return [w.lower() for w in _WORD_RE.findall(text or "")]


def score_text_emotions(text: str, lexicon: dict) -> dict:
    """Return {emotion: count} for every word in text found in the lexicon."""
    scores = {emotion: 0 for emotion in EMOTIONS}
    for word in tokenize(text):
        for emotion in lexicon.get(word, ()):
            scores[emotion] += 1
    return scores


def primary_emotion(text: str, lexicon: dict):
    """Return (primary_emotion_or_None, scores_dict).

    None means no emotion word from the lexicon was found in the text at all (every
    score is 0), a genuinely undetermined case, not silently defaulted to one emotion.
    Ties are broken by fixed alphabetical order over EMOTIONS.
    """
    scores = score_text_emotions(text, lexicon)
    max_score = max(scores.values())
    if max_score == 0:
        return None, scores
    for emotion in EMOTIONS:  # EMOTIONS is already alphabetical, defines the tie-break
        if scores[emotion] == max_score:
            return emotion, scores
    return None, scores  # unreachable, defensive
