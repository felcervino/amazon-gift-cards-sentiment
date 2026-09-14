"""Step 0: confirm Gift_Cards.jsonl.gz can be streamed and one line parses with required fields."""
import gzip
import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Gift_Cards.jsonl.gz")

REQUIRED_FIELDS = ["rating", "title", "text"]
KEPT_METADATA_FIELDS = ["verified_purchase", "helpful_vote", "timestamp"]


def main() -> None:
    line_count = 0
    first_record = None
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as f:
        for line in f:
            line_count += 1
            if first_record is None:
                first_record = json.loads(line)
            if line_count >= 1000:
                break

    print(f"Streamed {line_count} lines without loading the full file into memory.")
    print("First record raw keys:", sorted(first_record.keys()))

    for field in REQUIRED_FIELDS:
        assert field in first_record, f"Missing required field: {field}"
    print("All required fields present:", REQUIRED_FIELDS)

    for field in KEPT_METADATA_FIELDS:
        assert field in first_record, f"Missing kept metadata field: {field}"
    print("All kept metadata fields present:", KEPT_METADATA_FIELDS)

    print("First record sample:")
    print(json.dumps(first_record, indent=2)[:1000])


if __name__ == "__main__":
    main()
