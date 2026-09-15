"""Step 6: three-class scoring, imbalanced (first 100) vs balanced (~50/class), compared.

Two runs, both using the same three-class prompt/parser/answer-key so the comparison is
apples-to-apples:
1. "Imbalanced": the same first 100 reviews used throughout Steps 2 and 5, re-scored with
   the new three-class prompt (this is a genuinely new set of calls; Step 2's binary
   results are not directly comparable to three-class labels).
2. "Balanced": a fixed-seed random sample of ~50 reviews per class drawn from the whole
   file (src/balanced_sampler.py).

Kept as a separate labeled run from Steps 1-5 (confirmed with Felipe), not replacing
their outputs. Results cached by review id, bounded retry/backoff, same pattern as
Steps 2 and 5.
"""
import gzip
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

import requests

from balanced_sampler import DEFAULT_N_PER_CLASS, DEFAULT_SEED, build_balanced_sample
from three_class_answer_key import three_class_answer_key
from three_class_prompt import classify
from three_class_response_parser import parse_three_class_response

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Gift_Cards.jsonl.gz")
CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "step6_cache.json")

IMBALANCED_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "step6_imbalanced_results.json")
BALANCED_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "step6_balanced_results.json")
SUMMARY_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "step6_summary.json")

IMBALANCED_BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2

LABELS = ("POSITIVE", "NEUTRAL", "NEGATIVE")


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


def score_records(records, cache, cache_key_prefix, call_counter):
    """Score a list of records with the three-class prompt, using/populating cache.
    cache_key_prefix distinguishes imbalanced vs balanced cache entries for the same
    review id, since the same review could appear in both (though unlikely at this
    scale) and, more importantly, keeps the two runs' cache entries unambiguous."""
    results = []
    for record in records:
        review_id = record["_review_id"]
        cache_key = f"{cache_key_prefix}:{review_id}"
        answer = three_class_answer_key(record.get("rating"))

        if cache_key in cache:
            raw = cache[cache_key]
        else:
            raw = classify_with_retry(record["title"], record["text"])
            cache[cache_key] = raw
            call_counter[0] += 1

        parsed = parse_three_class_response(raw)

        match = None
        if answer.status == "ok" and parsed.status == "ok":
            match = answer.label == parsed.label

        results.append({
            "review_id": review_id,
            "title": record["title"],
            "text": record["text"],
            "rating": record.get("rating"),
            "sample_label": record.get("_sample_label"),
            "answer_key_status": answer.status,
            "answer_key_label": answer.label,
            "raw_model_response": raw,
            "parsed_status": parsed.status,
            "parsed_label": parsed.label,
            "match": match,
        })
    return results


def confusion_matrix(results):
    matrix = {actual: {predicted: 0 for predicted in LABELS} for actual in LABELS}
    for r in results:
        if r["answer_key_status"] == "ok" and r["parsed_status"] == "ok":
            matrix[r["answer_key_label"]][r["parsed_label"]] += 1
    return matrix


def per_class_accuracy(results):
    out = {}
    for label in LABELS:
        rows = [r for r in results if r["answer_key_status"] == "ok" and r["parsed_status"] == "ok"
                and r["answer_key_label"] == label]
        n = len(rows)
        n_correct = sum(1 for r in rows if r["match"])
        out[label] = {"n": n, "n_correct": n_correct, "accuracy": (n_correct / n) if n else None}
    return out


def overall_agreement(results):
    valid = [r for r in results if r["answer_key_status"] == "ok" and r["parsed_status"] == "ok"]
    n_valid = len(valid)
    n_match = sum(1 for r in valid if r["match"])
    return {
        "n_valid": n_valid,
        "n_match": n_match,
        "rate": (n_match / n_valid) if n_valid else None,
    }


def main():
    cache = load_cache()
    call_counter = [0]

    # 1. Imbalanced: same first 100 reviews as Steps 2/5, re-scored with the three-class
    #    prompt.
    imbalanced_records = load_first_n(IMBALANCED_BATCH_SIZE)
    imbalanced_results = score_records(imbalanced_records, cache, "imbalanced", call_counter)

    # 2. Balanced: ~50 per class, fixed seed, drawn from the whole file.
    balanced_records, sampled_indices, buckets = build_balanced_sample(
        n_per_class=DEFAULT_N_PER_CLASS, seed=DEFAULT_SEED
    )
    balanced_results = score_records(balanced_records, cache, "balanced", call_counter)

    save_cache(cache)

    os.makedirs(os.path.dirname(IMBALANCED_RESULTS_PATH), exist_ok=True)
    with open(IMBALANCED_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(imbalanced_results, f, indent=2)
    with open(BALANCED_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(balanced_results, f, indent=2)

    imbalanced_class_balance = {
        label: sum(1 for r in imbalanced_results if r["answer_key_status"] == "ok" and r["answer_key_label"] == label)
        for label in LABELS
    }
    balanced_class_balance = {
        label: sum(1 for r in balanced_results if r["answer_key_status"] == "ok" and r["answer_key_label"] == label)
        for label in LABELS
    }

    summary = {
        "imbalanced": {
            "batch_description": "first 100 reviews in file order, same set as Steps 2 and 5",
            "class_balance": imbalanced_class_balance,
            "overall_agreement": overall_agreement(imbalanced_results),
            "per_class_accuracy": per_class_accuracy(imbalanced_results),
            "confusion_matrix": confusion_matrix(imbalanced_results),
        },
        "balanced": {
            "batch_description": f"~{DEFAULT_N_PER_CLASS} per class, fixed seed {DEFAULT_SEED}, drawn from the whole file",
            "seed": DEFAULT_SEED,
            "n_per_class_requested": DEFAULT_N_PER_CLASS,
            "pool_sizes_in_full_dataset": {label: len(buckets.get(label, [])) for label in LABELS},
            "class_balance": balanced_class_balance,
            "overall_agreement": overall_agreement(balanced_results),
            "per_class_accuracy": per_class_accuracy(balanced_results),
            "confusion_matrix": confusion_matrix(balanced_results),
        },
        "new_endpoint_calls_this_run": call_counter[0],
        "model": "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit",
        "temperature": 0,
        "enable_thinking": False,
    }

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"New endpoint calls this run: {call_counter[0]}")
    print(f"Imbalanced results: {IMBALANCED_RESULTS_PATH}")
    print(f"Balanced results: {BALANCED_RESULTS_PATH}")
    print(f"Summary: {SUMMARY_PATH}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
