"""Step 2: score the first 100 rows against the rating-derived answer key.

The model never receives the rating. Results are cached per review id (the row's line
index in the source file, since the dataset has no unique review id field) so a re-run
never needlessly re-calls the endpoint for a row already classified. Basic bounded
retry/backoff on transient failures, no infinite retry loops.
"""
import gzip
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

import requests

from answer_key import binary_answer_key
from response_parser import parse_response
from sentiment_prompt import classify

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Gift_Cards.jsonl.gz")
CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "step2_cache.json")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "step2_results.json")
SUMMARY_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "step2_summary.json")

BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2


def load_first_n(n: int):
    records = []
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            record = json.loads(line)
            record["_review_id"] = i
            records.append(record)
    return records


def load_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict) -> None:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def classify_with_retry(title: str, text: str) -> str:
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return classify(title, text)
        except requests.exceptions.RequestException as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    raise RuntimeError(f"classify failed after {MAX_RETRIES} attempts: {last_error}")


def main():
    records = load_first_n(BATCH_SIZE)
    cache = load_cache()

    call_count = 0
    results = []

    for record in records:
        review_id = str(record["_review_id"])
        answer = binary_answer_key(record.get("rating"))

        if review_id in cache:
            raw = cache[review_id]
        else:
            raw = classify_with_retry(record["title"], record["text"])
            cache[review_id] = raw
            call_count += 1

        parsed = parse_response(raw)

        match = None
        if answer.status == "ok" and parsed.status == "ok":
            match = answer.label == parsed.label

        results.append({
            "review_id": record["_review_id"],
            "title": record["title"],
            "text": record["text"],
            "rating": record.get("rating"),
            "answer_key_status": answer.status,
            "answer_key_label": answer.label,
            "answer_key_error": answer.error,
            "raw_model_response": raw,
            "parsed_status": parsed.status,
            "parsed_label": parsed.label,
            "parsed_error": parsed.error,
            "match": match,
        })

    save_cache(cache)

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    summary = compute_summary(results, call_count)
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Scored {len(results)} reviews. New endpoint calls this run: {call_count} "
          f"(cached: {len(results) - call_count}).")
    print(f"Results saved to {RESULTS_PATH}")
    print(f"Summary saved to {SUMMARY_PATH}")
    print(json.dumps(summary, indent=2))


def compute_summary(results, call_count):
    valid = [r for r in results if r["answer_key_status"] == "ok" and r["parsed_status"] == "ok"]
    flagged_rating = [r for r in results if r["answer_key_status"] != "ok"]
    flagged_parse = [r for r in results if r["parsed_status"] != "ok"]

    n_valid = len(valid)
    n_matches = sum(1 for r in valid if r["match"])
    agreement_rate = n_matches / n_valid if n_valid else None

    class_balance = {"POSITIVE": 0, "NEGATIVE": 0}
    for r in valid:
        class_balance[r["answer_key_label"]] += 1

    per_class_accuracy = {}
    for label in ("POSITIVE", "NEGATIVE"):
        class_rows = [r for r in valid if r["answer_key_label"] == label]
        n_class = len(class_rows)
        n_class_correct = sum(1 for r in class_rows if r["match"])
        per_class_accuracy[label] = {
            "n": n_class,
            "n_correct": n_class_correct,
            "accuracy": (n_class_correct / n_class) if n_class else None,
        }

    mismatches = [
        {
            "review_id": r["review_id"],
            "rating": r["rating"],
            "answer_key_label": r["answer_key_label"],
            "parsed_label": r["parsed_label"],
            "title": r["title"],
        }
        for r in valid if not r["match"]
    ]

    return {
        "total_reviews": len(results),
        "n_valid_for_scoring": n_valid,
        "n_flagged_rating": len(flagged_rating),
        "n_flagged_parse": len(flagged_parse),
        "overall_agreement_rate": agreement_rate,
        "class_balance_from_answer_key": class_balance,
        "class_balance_note": (
            f"{class_balance['POSITIVE']} of {n_valid} rows ("
            f"{class_balance['POSITIVE'] / n_valid * 100:.1f}%) are POSITIVE by the rating "
            "answer key. The data is heavily skewed toward high ratings; a high overall "
            "agreement rate on this batch does not by itself mean the model is strong on "
            "the minority NEGATIVE class." if n_valid else None
        ),
        "per_class_accuracy": per_class_accuracy,
        "mismatches": mismatches,
        "new_endpoint_calls_this_run": call_count,
        "model": "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit",
        "temperature": 0,
        "enable_thinking": False,
    }


if __name__ == "__main__":
    main()
