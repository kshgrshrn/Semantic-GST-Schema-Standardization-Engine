"""Benchmark evaluator for schema mapping quality."""

from __future__ import annotations

import random
import time
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


def build_test_set(headers: List[str]) -> List[Tuple[str, str]]:
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


def run_benchmark(
    model: SentenceTransformer,
    test_cases: List[Tuple[str, str]],
    schema_embeddings,
) -> Dict[str, float]:
    top1, top3 = 0, 0
    cosine_scores: List[float] = []

    for noisy_col, true_col in test_cases:
        query_emb = model.encode(noisy_col)
        scores = cos_sim(query_emb, schema_embeddings)[0].tolist()

        ranked = np.argsort(scores)[::-1]
        best_match = CANONICAL_HEADERS[ranked[0]]
        best_score = scores[ranked[0]]
        top3_matches = [CANONICAL_HEADERS[i] for i in ranked[:3]]

        cosine_scores.append(best_score)
        if best_match == true_col:
            top1 += 1
        if true_col in top3_matches:
            top3 += 1

    n = len(test_cases)
    return {
        "top1_acc": top1 / n * 100,
        "top3_acc": top3 / n * 100,
        "avg_cosine": sum(cosine_scores) / n * 100,
    }


def print_results(label: str, results: Dict[str, float], n: int, elapsed: float) -> None:
    latency_ms = (elapsed / n) * 1000
    print(f"\n  Model : {label}")
    print(f"  Top-1 Accuracy        : {results['top1_acc']:.2f}%")
    print(f"  Top-3 Accuracy        : {results['top3_acc']:.2f}%")
    print(f"  Avg Top-1 Cosine Sim  : {results['avg_cosine']:.2f}%")
    print(f"  Latency per column    : {latency_ms:.2f} ms")


def main() -> None:
    test_cases = build_test_set(CANONICAL_HEADERS)
    n = len(test_cases)
    print(
        f"\nTest set built: {n} synthetic permutations across "
        f"{len(CANONICAL_HEADERS)} canonical fields (seed=42)"
    )
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
    print(f"Test cases    : {n} synthetic permutations (fixed seed=42)")

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
