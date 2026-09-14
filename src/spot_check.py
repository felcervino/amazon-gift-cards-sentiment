"""Step 1 spot-check: a small, manually chosen set of obvious positive/negative reviews.

Each review below was picked by reading its title/text directly (see src/dump_sample_reviews.py
for how candidates were surfaced). The line_index and star rating are recorded only for
traceability back to the source file; the model never receives the rating.
"""
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from response_parser import parse_response
from sentiment_prompt import classify

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Gift_Cards.jsonl.gz")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "step1_spot_check.json")

# (line_index, expected_label), hand-picked by reading text/title in dump_sample_reviews.py.
MANUAL_PICKS = [
    (5, "POSITIVE"),    # "Cute!" / "That snowman tin is adorable"
    (10, "POSITIVE"),   # "Convenient, safe, and perfect gift" / grandson loves his gift cards
    (57, "POSITIVE"),   # "who wouldn't LOVE this?!? Wonderful gift for any occasion."
    (15, "NEGATIVE"),   # "One Star" / "Card did not work!!!!"
    (199, "NEGATIVE"),  # "One of the worst." / thoroughly disappointed and frustrated
    (629, "NEGATIVE"),  # "Card was invalid void not activated...." / would give zero stars
]


def load_records_by_index(indices):
    wanted = set(indices)
    found = {}
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i in wanted:
                found[i] = json.loads(line)
            if len(found) == len(wanted):
                break
    return found


def main():
    indices = [idx for idx, _ in MANUAL_PICKS]
    records = load_records_by_index(indices)

    results = []
    for idx, expected in MANUAL_PICKS:
        record = records[idx]
        raw = classify(record["title"], record["text"])
        parsed = parse_response(raw)
        results.append({
            "line_index": idx,
            "title": record["title"],
            "text": record["text"],
            "star_rating_context_only": record["rating"],
            "expected_obvious_label": expected,
            "raw_model_response": raw,
            "parsed_status": parsed.status,
            "parsed_label": parsed.label,
            "match": parsed.label == expected,
        })

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Saved {len(results)} spot-check results to {OUTPUT_PATH}")
    n_match = sum(1 for r in results if r["match"])
    for r in results:
        status = "MATCH" if r["match"] else "MISMATCH"
        print(f"[{status}] line={r['line_index']} expected={r['expected_obvious_label']} got={r['parsed_label']} (status={r['parsed_status']}) title={r['title']!r}")
    print(f"\n{n_match}/{len(results)} matched the manually expected label.")


if __name__ == "__main__":
    main()
