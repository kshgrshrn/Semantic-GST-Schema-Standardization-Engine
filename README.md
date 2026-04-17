# Semantic GST Schema Standardization Engine

An NLP pipeline that maps messy, inconsistent client Excel headers to a clean, unified 61-field tax schema using sentence embeddings.

**Built during an EY internship and approved for presentation to senior engineers.**

---

## The Problem

When ingesting tax data (GSTR-1, GSTR-2A, purchase registers) from different clients, the same field shows up under completely different names:

| What the client sends | What the schema expects |
| --------------------- | ----------------------- |
| `Name of Supplier`  | `SupplierName`        |
| `Supplier GST No`   | `SupplierGSTIN`       |
| `Value Of Invoice`  | `InvoiceValue`        |
| `IGST Amt`          | `IntegratedTaxAmount` |

The old way of solving this: writing giant Python dictionaries (`if col == "Name of Supplier"`) to handle every possible variation. This breaks the moment a new client uses a slightly different name.

This project solves it by using a Hugging Face Sentence Transformer to understand what the header *means* and map it correctly, without any hardcoded rules.

---

## How It Works

1. **Extraction:** Reads the raw `.xlsx` file with Pandas.
2. **Embedding:** Converts the column headers into vector embeddings using `all-MiniLM-L6-v2`.
3. **Similarity Matching:** Computes cosine similarity against all 61 canonical GST headers.
4. **Output:** If similarity > 0.5, the column gets renamed and the clean, standardized file is saved as `renamed.xlsx`. The 0.5 threshold was chosen as a conservative lower bound to avoid incorrect mappings on ambiguous or highly abbreviated headers.

---

## Performance

To measure how the system actually holds up, `evaluate_metrics.py` builds a deterministic benchmark of 255 synthetic, noisy header variants (abbreviations, missing spaces, all-caps) across all 61 fields (seed=42, fully reproducible).

The model was fine-tuned on domain-specific (noisy_header, canonical_header) pairs derived from real GST file variations observed during the internship. Training data is excluded from this repo for confidentiality reasons.

|                                       | Baseline (`all-MiniLM-L6-v2`) | Fine-tuned (`semantic_renamer_model`) |
| ------------------------------------- | ------------------------------- | --------------------------------------- |
| **Top-1 Accuracy**              | 89.80%                          | 88.63%                                  |
| **Top-3 Accuracy**              | 98.04%                          | 98.04%                                  |
| **Avg Top-1 Cosine Similarity** | 86.78%                          | **94.88%** (+8.1%)                |
| **Latency per column**          | 6.46 ms                         | **4.16 ms** (35% faster)          |

**On Fine-Tuning:** The base model already generalizes very well to English header variations, so raw Top-1 accuracy didn't shift significantly after domain fine-tuning. The measurable gains were in cosine similarity confidence (+8.1%, from 86.78% to 94.88%) and inference latency (35% faster, 6.46ms to 4.16ms). In practice, the higher similarity margin matters: it means the 0.5 threshold rejects fewer valid matches as false negatives, reducing the volume of headers flagged for manual review.

---

## Quick Start

```bash
# TODO: replace with your actual repo URL once published
git clone https://github.com/yourusername/semantic-gst-schema-engine.git
cd semantic-gst-schema-engine

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

```bash
# Run the standardizer on an input file
python standardize.py

# Run the benchmark to reproduce the metrics above (seed=42)
python evaluate_metrics.py
```

A sanitized demo input/output pair is in `sample_data/` if you want to see what the transformation looks like without needing the original files.

---

## Project Structure

```
standardize.py        # Core inference pipeline: maps input headers to canonical schema
model_training.py     # Fine-tuning script: trains MiniLM on domain-specific header pairs
evaluate_metrics.py   # Benchmark: baseline vs fine-tuned, Top-1/Top-3/latency (seed=42)
requirements.txt      # Pinned dependencies
sample_data/
    sample_input.xlsx   # Anonymized example of a real messy client file
    sample_output.xlsx  # Expected output after standardization
```

---

## What Could Be Better (V2 Ideas)

- **Hard Negatives in Training:** Explicitly teach the model what is *not* a good match, so near-neighbor fields like IGST vs CGST don't get confused.
- **Collision Handling:** If two input columns map to the same target, flag it for review instead of silently overwriting.
- **Threshold Calibration:** Replace the fixed 0.5 cutoff with one tuned on a proper validation split.
