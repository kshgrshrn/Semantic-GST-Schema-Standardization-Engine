"""Benchmark evaluator for schema mapping quality."""

from __future__ import annotations

import json
import os
import random
import time
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from .schema import CANONICAL_HEADERS

random.seed(42)
np.random.seed(42)

NOISE_PATTERNS = {
    "Number": ["No", "Num", "#", "Nmr", "Code"],
    "Date": ["Dt", "Date of", "Dated"],
    "Amount": ["Amt", "Amnt", "Value", "Total"],
    "GSTIN": ["GST No", "GST ID", "Tax ID", "GSTIN No"],
    "Value": ["Val", "Amount", "Total Value"],
    "Identifier": ["ID", "Flag"],
    "Supplier": ["Vendor", "Seller", "Party"],
    "Rate": ["%", "Pct", "Percent"],
    "Available": ["Avail", "Eligible"],
    "Integrated": ["IGST", "Inter-state"],
    "Central": ["CGST"],
    "State": ["SGST", "UT"],
}

# Default path for the external annotated eval set.
_EVAL_SET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "tests", "data", "eval_set.jsonl",
)


def build_test_set(headers: List[str]) -> List[Tuple[str, str]]:
    """Generate synthetic noisy header variants (fallback when no external eval set)."""
    test_cases: List[Tuple[str, str]] = []
    for true_col in headers:
        test_cases.append((true_col, true_col))

        spaced = "".join([" " + c if c.isupper() else c for c in true_col]).strip().lower()
        test_cases.append((spaced, true_col))

        test_cases.append((true_col.upper(), true_col))

        for word, substitutes in NOISE_PATTERNS.items():
            if word in true_col:
                abbr = true_col.replace(word, substitutes[0])
                test_cases.append((abbr, true_col))
                test_cases.append((abbr.lower(), true_col))
                break

    random.shuffle(test_cases)
    return test_cases


def load_eval_set(path: str) -> List[Tuple[str, str]]:
    """Load an external annotated eval set from JSONL.

    Each line must have ``"noisy"`` and ``"canonical"`` keys.
    """
    test_cases: List[Tuple[str, str]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            test_cases.append((entry["noisy"], entry["canonical"]))
    return test_cases


def run_benchmark(
    model: SentenceTransformer,
    test_cases: List[Tuple[str, str]],
    schema_embeddings,
) -> Dict:
    """Run the benchmark and return detailed results including per-field stats."""
    top1, top3 = 0, 0
    cosine_scores: List[float] = []
    confusions: List[Tuple[str, str, str, float]] = []  # (noisy, expected, predicted, score)

    # Per-field tracking for precision/recall.
    per_field_tp: Dict[str, int] = defaultdict(int)
    per_field_fp: Dict[str, int] = defaultdict(int)
    per_field_fn: Dict[str, int] = defaultdict(int)

    # Batch encode all noisy columns at once.
    noisy_texts = [nc for nc, _ in test_cases]
    query_embeddings = model.encode(noisy_texts, show_progress_bar=False)
    all_scores = cos_sim(query_embeddings, schema_embeddings).cpu().numpy()

    for idx, (noisy_col, true_col) in enumerate(test_cases):
        scores = all_scores[idx]
        ranked = np.argsort(scores)[::-1]
        best_match = CANONICAL_HEADERS[ranked[0]]
        best_score = float(scores[ranked[0]])
        top3_matches = [CANONICAL_HEADERS[i] for i in ranked[:3]]

        cosine_scores.append(best_score)
        if best_match == true_col:
            top1 += 1
            per_field_tp[true_col] += 1
        else:
            per_field_fn[true_col] += 1
            per_field_fp[best_match] += 1
            confusions.append((noisy_col, true_col, best_match, best_score))

        if true_col in top3_matches:
            top3 += 1

    n = len(test_cases)

    # Compute per-field precision, recall, F1.
    per_field_metrics: Dict[str, Dict[str, float]] = {}
    all_fields = set(per_field_tp) | set(per_field_fp) | set(per_field_fn)
    for field in sorted(all_fields):
        tp = per_field_tp[field]
        fp = per_field_fp[field]
        fn = per_field_fn[field]
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_field_metrics[field] = {"precision": precision, "recall": recall, "f1": f1}

    # Macro averages.
    fields_with_data = [m for m in per_field_metrics.values() if m["f1"] > 0 or m["precision"] > 0 or m["recall"] > 0]
    if fields_with_data:
        macro_precision = sum(m["precision"] for m in fields_with_data) / len(fields_with_data)
        macro_recall = sum(m["recall"] for m in fields_with_data) / len(fields_with_data)
        macro_f1 = sum(m["f1"] for m in fields_with_data) / len(fields_with_data)
    else:
        macro_precision = macro_recall = macro_f1 = 0.0

    return {
        "top1_acc": top1 / n * 100,
        "top3_acc": top3 / n * 100,
        "avg_cosine": sum(cosine_scores) / n * 100,
        "macro_precision": macro_precision * 100,
        "macro_recall": macro_recall * 100,
        "macro_f1": macro_f1 * 100,
        "confusions": confusions,
        "per_field_metrics": per_field_metrics,
    }


def print_results(label: str, results: Dict, n: int, elapsed: float) -> None:
    latency_ms = (elapsed / n) * 1000
    print(f"\n  Model : {label}")
    print(f"  Top-1 Accuracy        : {results['top1_acc']:.2f}%")
    print(f"  Top-3 Accuracy        : {results['top3_acc']:.2f}%")
    print(f"  Avg Top-1 Cosine Sim  : {results['avg_cosine']:.2f}%")
    print(f"  Macro Precision       : {results['macro_precision']:.2f}%")
    print(f"  Macro Recall          : {results['macro_recall']:.2f}%")
    print(f"  Macro F1              : {results['macro_f1']:.2f}%")
    print(f"  Latency per column    : {latency_ms:.2f} ms")

    confusions = results.get("confusions", [])
    if confusions:
        print(f"\n  Top confused pairs ({min(10, len(confusions))} shown):")
        for noisy, expected, predicted, score in confusions[:10]:
            print(f"    '{noisy}' -> expected '{expected}', got '{predicted}' (score={score:.4f})")


def main() -> None:
    # Prefer external eval set if available; fall back to synthetic.
    if os.path.exists(_EVAL_SET_PATH):
        test_cases = load_eval_set(_EVAL_SET_PATH)
        eval_source = f"external eval set ({_EVAL_SET_PATH})"
    else:
        test_cases = build_test_set(CANONICAL_HEADERS)
        eval_source = "synthetic permutations (built-in, seed=42)"

    n = len(test_cases)
    print(
        f"\nTest set built: {n} cases across "
        f"{len(CANONICAL_HEADERS)} canonical fields"
    )
    print(f"Source: {eval_source}")
    print("=" * 60)

    print("\nLoading baseline model (all-MiniLM-L6-v2)...")
    base_model = SentenceTransformer("all-MiniLM-L6-v2")
    base_schema_embs = base_model.encode(CANONICAL_HEADERS)
    t0 = time.time()
    base_results = run_benchmark(base_model, test_cases, base_schema_embs)
    base_time = time.time() - t0

    print("Loading fine-tuned model (semantic_renamer_model)...")
    try:
        ft_model = SentenceTransformer("semantic_renamer_model")
    except Exception:
        print("Could not find semantic_renamer_model - skipping fine-tuned comparison.")
        ft_model = None

    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Schema size   : {len(CANONICAL_HEADERS)} canonical fields")
    print(f"Test cases    : {n} ({eval_source})")

    print_results("Baseline  - all-MiniLM-L6-v2 (no fine-tuning)", base_results, n, base_time)

    if ft_model:
        ft_schema_embs = ft_model.encode(CANONICAL_HEADERS)
        t0 = time.time()
        ft_results = run_benchmark(ft_model, test_cases, ft_schema_embs)
        ft_time = time.time() - t0
        print_results("Fine-tuned - semantic_renamer_model", ft_results, n, ft_time)

        uplift = ft_results["top1_acc"] - base_results["top1_acc"]
        print(f"\n  Fine-tuning uplift (Top-1) : {uplift:+.2f}%")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
