"""Utility: dump a readable slice of reviews so a human/agent can manually pick obvious
positive/negative examples for the Step 1 spot-check, rather than picking by keyword rule.

Rating is shown only to narrow which part of the file to read (low-rated reviews are more
likely to contain negative sentiment); the actual pick is made by reading the text, and the
model never sees the rating.
"""
import argparse
import gzip
import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Gift_Cards.jsonl.gz")


def main(n: int, max_rating: float, min_rating: float):
    shown = 0
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if shown >= n:
                break
            record = json.loads(line)
            rating = record.get("rating")
            if rating is None or rating < min_rating or rating > max_rating:
                continue
            title = (record.get("title") or "").replace("\n", " ")
            text = (record.get("text") or "").replace("\n", " ")
            print(f"[{i}] rating={rating} title={title!r}")
            print(f"     text={text[:220]!r}")
            shown += 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--max-rating", type=float, default=5.0)
    ap.add_argument("--min-rating", type=float, default=1.0)
    args = ap.parse_args()
    main(args.n, args.max_rating, args.min_rating)
