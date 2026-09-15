"""Step 6 unit tests for src/balanced_sampler.py, written before running it on the real
gzip file. Uses a small synthetic gzip file so tests run fast and don't depend on the
(gitignored) real dataset being present. Explicitly confirms the sampler returns the
requested count per class, not an assumed-correct count, per PLAN.md Section 11.
"""
import gzip
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from balanced_sampler import build_index_buckets, fetch_records_by_index, sample_balanced_indices


def make_synthetic_gzip(path, rating_sequence):
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for i, rating in enumerate(rating_sequence):
            record = {
                "rating": rating,
                "title": f"title {i}",
                "text": f"text {i}",
            }
            f.write(json.dumps(record) + "\n")


class TestBuildIndexBuckets(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmpdir.name, "synthetic.jsonl.gz")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_buckets_by_three_class_label(self):
        # 10 POSITIVE (4,5), 4 NEUTRAL (3), 6 NEGATIVE (1,2), plus 2 invalid ratings.
        ratings = [5.0] * 5 + [4.0] * 5 + [3.0] * 4 + [2.0] * 3 + [1.0] * 3 + [None, 7.0]
        make_synthetic_gzip(self.path, ratings)
        buckets = build_index_buckets(self.path)
        self.assertEqual(len(buckets["POSITIVE"]), 10)
        self.assertEqual(len(buckets["NEUTRAL"]), 4)
        self.assertEqual(len(buckets["NEGATIVE"]), 6)
        # Invalid ratings must not land in any bucket.
        total_bucketed = sum(len(v) for v in buckets.values())
        self.assertEqual(total_bucketed, 20)  # 22 rows minus 2 invalid


class TestSampleBalancedIndices(unittest.TestCase):
    def test_returns_exactly_n_per_class_when_pool_is_large_enough(self):
        buckets = {
            "POSITIVE": list(range(0, 200)),
            "NEUTRAL": list(range(200, 400)),
            "NEGATIVE": list(range(400, 600)),
        }
        sampled = sample_balanced_indices(buckets, n_per_class=50, seed=42)
        self.assertEqual(len(sampled["POSITIVE"]), 50)
        self.assertEqual(len(sampled["NEUTRAL"]), 50)
        self.assertEqual(len(sampled["NEGATIVE"]), 50)

    def test_returns_full_pool_when_pool_smaller_than_n_per_class(self):
        buckets = {
            "POSITIVE": list(range(0, 200)),
            "NEUTRAL": [1, 2, 3],  # only 3 available, fewer than the requested 50
            "NEGATIVE": list(range(400, 600)),
        }
        sampled = sample_balanced_indices(buckets, n_per_class=50, seed=42)
        self.assertEqual(len(sampled["NEUTRAL"]), 3)
        self.assertEqual(sorted(sampled["NEUTRAL"]), [1, 2, 3])

    def test_same_seed_gives_same_sample(self):
        buckets = {
            "POSITIVE": list(range(0, 300)),
            "NEUTRAL": list(range(300, 600)),
            "NEGATIVE": list(range(600, 900)),
        }
        sampled_a = sample_balanced_indices(buckets, n_per_class=50, seed=42)
        sampled_b = sample_balanced_indices(buckets, n_per_class=50, seed=42)
        self.assertEqual(sampled_a, sampled_b)

    def test_different_seed_gives_different_sample(self):
        buckets = {
            "POSITIVE": list(range(0, 300)),
            "NEUTRAL": list(range(300, 600)),
            "NEGATIVE": list(range(600, 900)),
        }
        sampled_a = sample_balanced_indices(buckets, n_per_class=50, seed=42)
        sampled_b = sample_balanced_indices(buckets, n_per_class=50, seed=99)
        self.assertNotEqual(sampled_a, sampled_b)

    def test_sampled_indices_are_all_within_their_pool(self):
        buckets = {
            "POSITIVE": list(range(0, 100)),
            "NEUTRAL": list(range(100, 150)),
            "NEGATIVE": list(range(150, 300)),
        }
        sampled = sample_balanced_indices(buckets, n_per_class=50, seed=7)
        for label, indices in sampled.items():
            for idx in indices:
                self.assertIn(idx, buckets[label])


class TestFetchRecordsByIndex(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmpdir.name, "synthetic.jsonl.gz")
        ratings = [5.0] * 20 + [3.0] * 20 + [1.0] * 20
        make_synthetic_gzip(self.path, ratings)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_fetches_exactly_the_requested_indices(self):
        indices_by_label = {"POSITIVE": [0, 5, 10], "NEUTRAL": [20, 25], "NEGATIVE": [40]}
        records = fetch_records_by_index(indices_by_label, self.path)
        self.assertEqual(len(records), 6)
        fetched_ids = sorted(r["_review_id"] for r in records)
        self.assertEqual(fetched_ids, [0, 5, 10, 20, 25, 40])

    def test_sample_label_tag_is_correct(self):
        indices_by_label = {"POSITIVE": [0], "NEUTRAL": [20], "NEGATIVE": [40]}
        records = fetch_records_by_index(indices_by_label, self.path)
        by_id = {r["_review_id"]: r for r in records}
        self.assertEqual(by_id[0]["_sample_label"], "POSITIVE")
        self.assertEqual(by_id[20]["_sample_label"], "NEUTRAL")
        self.assertEqual(by_id[40]["_sample_label"], "NEGATIVE")


if __name__ == "__main__":
    unittest.main()
