"""Step 7: compute and save the full dataset's star-rating distribution.

Used for the descriptive star-rating distribution chart, to honestly show how skewed the
full dataset is toward high ratings (Guardrail: "Be honest about imbalance"), not just the
already-balanced Step 6 sample. Saved to a file so the chart's numbers trace back to a
saved computation, never typed in by hand.
"""
import gzip
import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Gift_Cards.jsonl.gz")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "dataset_rating_distribution.json")


def main():
    counts = {"1.0": 0, "2.0": 0, "3.0": 0, "4.0": 0, "5.0": 0}
    n_total = 0
    n_flagged = 0

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as f:
        for line in f:
            n_total += 1
            record = json.loads(line)
            rating = record.get("rating")
            key = str(rating)
            if key in counts:
                counts[key] += 1
            else:
                n_flagged += 1

    result = {
        "total_reviews": n_total,
        "counts_by_rating": counts,
        "n_flagged_unexpected_rating": n_flagged,
        "source_file": "data/Gift_Cards.jsonl.gz",
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
