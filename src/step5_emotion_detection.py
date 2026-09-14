"""Step 5: two independent primary-emotion detections, compared.

1. LLM: the same 100 reviews from Step 2, re-run with the extended sentiment+emotion
   prompt (confirmed scope with Felipe: replaces the Step 2-era cache with a new
   Step-5-specific cache, same 100 reviews, one combined call per review).
2. NRC word list: derived from the same review text already saved, no model calls.

Both are saved per review alongside an agreement/disagreement flag. Results cached by
review id so a re-run never needlessly re-calls the endpoint. Bounded retry/backoff on
transient failures, same pattern as Step 2.
"""
import gzip
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

import requests

from answer_key import binary_answer_key
from emotion_prompt import classify
from emotion_response_parser import parse_emotion_response
from nrc_lexicon import load_lexicon, primary_emotion

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Gift_Cards.jsonl.gz")
CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "step5_cache.json")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "step5_results.json")
SUMMARY_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "step5_summary.json")

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
    lexicon = load_lexicon()

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

        parsed = parse_emotion_response(raw)

        nrc_emotion, nrc_scores = primary_emotion(record["text"], lexicon)

        emotion_match = None
        if parsed.status == "ok" and nrc_emotion is not None:
            emotion_match = parsed.emotion == nrc_emotion

        sentiment_match = None
        if answer.status == "ok" and parsed.status == "ok":
            sentiment_match = answer.label == parsed.label

        results.append({
            "review_id": record["_review_id"],
            "title": record["title"],
            "text": record["text"],
            "rating": record.get("rating"),
            "answer_key_status": answer.status,
            "answer_key_label": answer.label,
            "raw_model_response": raw,
            "parsed_status": parsed.status,
            "llm_label": parsed.label,
            "llm_emotion": parsed.emotion,
            "sentiment_match": sentiment_match,
            "nrc_emotion": nrc_emotion,
            "nrc_scores": nrc_scores,
            "emotion_match": emotion_match,
        })

    save_cache(cache)

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    summary = compute_summary(results, call_count)
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Processed {len(results)} reviews. New endpoint calls this run: {call_count} "
          f"(cached: {len(results) - call_count}).")
    print(f"Results saved to {RESULTS_PATH}")
    print(f"Summary saved to {SUMMARY_PATH}")
    print(json.dumps(summary, indent=2))


def compute_summary(results, call_count):
    both_determined = [
        r for r in results
        if r["parsed_status"] == "ok" and r["nrc_emotion"] is not None
    ]
    n_both = len(both_determined)
    n_agree = sum(1 for r in both_determined if r["emotion_match"])
    agreement_rate = n_agree / n_both if n_both else None

    n_nrc_undetermined = sum(1 for r in results if r["nrc_emotion"] is None)
    n_llm_malformed = sum(1 for r in results if r["parsed_status"] != "ok")

    llm_emotion_counts = {}
    nrc_emotion_counts = {}
    for r in results:
        if r["llm_emotion"]:
            llm_emotion_counts[r["llm_emotion"]] = llm_emotion_counts.get(r["llm_emotion"], 0) + 1
        if r["nrc_emotion"]:
            nrc_emotion_counts[r["nrc_emotion"]] = nrc_emotion_counts.get(r["nrc_emotion"], 0) + 1

    disagreements = [
        {
            "review_id": r["review_id"],
            "title": r["title"],
            "llm_emotion": r["llm_emotion"],
            "nrc_emotion": r["nrc_emotion"],
            "nrc_scores": r["nrc_scores"],
        }
        for r in both_determined if not r["emotion_match"]
    ]

    return {
        "total_reviews": len(results),
        "n_both_methods_determined": n_both,
        "n_nrc_undetermined_no_lexicon_words": n_nrc_undetermined,
        "n_llm_malformed": n_llm_malformed,
        "emotion_agreement_rate": agreement_rate,
        "llm_emotion_distribution": llm_emotion_counts,
        "nrc_emotion_distribution": nrc_emotion_counts,
        "n_disagreements": len(disagreements),
        "disagreements": disagreements,
        "new_endpoint_calls_this_run": call_count,
        "model": "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit",
        "temperature": 0,
        "enable_thinking": False,
        "nrc_lexicon_source": "NRC Word-Emotion Association Lexicon (EmoLex), Saif Mohammad "
                               "and Peter Turney, National Research Council Canada",
    }


if __name__ == "__main__":
    main()
