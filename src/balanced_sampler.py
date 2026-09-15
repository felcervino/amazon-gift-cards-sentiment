"""Step 6: balanced three-class sample, fixed seed, drawn from the whole file.

Reading the first N rows in order under-represents the rarer classes (NEUTRAL/NEGATIVE
are a small minority in this dataset). Instead, scan the whole file once, bucket every
review's line index by its three-class answer-key label, then draw a fixed-seed random
sample of n_per_class from each bucket.
"""
import gzip
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))

from three_class_answer_key import three_class_answer_key

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Gift_Cards.jsonl.gz")

DEFAULT_SEED = 42
DEFAULT_N_PER_CLASS = 50


def build_index_buckets(data_path=DATA_PATH):
    """Scan the whole file once, return {label: [line_index, ...]} in file order."""
    buckets = {"POSITIVE": [], "NEUTRAL": [], "NEGATIVE": []}
    with gzip.open(data_path, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            record = json.loads(line)
            answer = three_class_answer_key(record.get("rating"))
            if answer.status == "ok":
                buckets[answer.label].append(i)
    return buckets


def sample_balanced_indices(buckets: dict, n_per_class: int = DEFAULT_N_PER_CLASS, seed: int = DEFAULT_SEED):
    """Return {label: [sampled_line_index, ...]}, up to n_per_class per label.

    Buckets are sorted before sampling so the result is reproducible regardless of
    dict/list construction order, given the same seed.
    """
    rng = random.Random(seed)
    sampled = {}
    for label in ("POSITIVE", "NEUTRAL", "NEGATIVE"):
        pool = sorted(buckets.get(label, []))
        k = min(n_per_class, len(pool))
        sampled[label] = sorted(rng.sample(pool, k))
    return sampled


def fetch_records_by_index(indices_by_label: dict, data_path=DATA_PATH):
    """Given {label: [line_index, ...]}, read those specific lines from the file and
    return a flat list of records, each tagged with _review_id (the line index) and
    _sample_label (which balanced-class bucket it was drawn for)."""
    wanted = {}
    for label, indices in indices_by_label.items():
        for idx in indices:
            wanted[idx] = label

    records = []
    with gzip.open(data_path, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i in wanted:
                record = json.loads(line)
                record["_review_id"] = i
                record["_sample_label"] = wanted[i]
                records.append(record)
    records.sort(key=lambda r: r["_review_id"])
    return records


def build_balanced_sample(n_per_class: int = DEFAULT_N_PER_CLASS, seed: int = DEFAULT_SEED, data_path=DATA_PATH):
    buckets = build_index_buckets(data_path)
    sampled_indices = sample_balanced_indices(buckets, n_per_class, seed)
    records = fetch_records_by_index(sampled_indices, data_path)
    return records, sampled_indices, buckets
