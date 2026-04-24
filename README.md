# GST Schema Standardization Engine

> Maps messy, inconsistent Excel headers from any client file
> to a unified 61-field GST schema using semantic embeddings, no hardcoded rules. 
>
> In proof-of-concept phase. (V2)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)]()

Built and deployed during an EY internship to automate tax data ingestion
across clients whose files use completely different column naming conventions.

---

**Business Impact During Internship:** Prior to this implementation, tax analysts spent an average of 20-30 minutes per client manually finding and mapping obscure legacy columns to the standard GSTR schema. By utilizing this pipeline, the initial mapping phase was entirely automated, **reducing manual ingestion time by roughly 85%** and eliminating human-error bottlenecks during the reconciliation process.

> [!IMPORTANT]
> **Data Privacy Note:** To strictly adhere to firm confidentiality and data privacy, all original client datasets, proprietary mapping dictionaries, and the actual fine-tuning corpus have been strictly excluded from this repository. The `sample_data/` and benchmarks provided here run entirely on synthetically generated header permutations.

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

This project solves it by using a Hugging Face Sentence Transformer to understand what the header _means_ and map it correctly, without any hardcoded rules.

---

## How It Works

```mermaid
flowchart LR
    A["Raw Excel Headers<br/>Inv No, GST No, IGST Amt"] --> B["Sentence Transformer<br/>MiniLM embeddings"]
    B --> C["Cosine Similarity Search<br/>against 61 canonical fields"]
    C --> D["Argmax Best Match<br/>per input column"]
    D --> E["Header Renaming / Threshold Check"]
    E --> F["Standardized 61-Field Output Schema"]
```

1. **Extraction:** Reads the raw `.xlsx` file with Pandas.
2. **Embedding:** Converts the column headers into vector embeddings using `all-MiniLM-L6-v2`.
3. **Similarity Matching:** Computes cosine similarity against all 61 canonical GST headers.
4. **Output:** If similarity > 0.5, the column gets renamed and the clean, standardized file is saved as `renamed.xlsx`. The 0.5 threshold was chosen as a conservative lower bound to avoid incorrect mappings on ambiguous or highly abbreviated headers.

### Core Tech Stack

- **`sentence-transformers`**: Provides the core NLP backbone (leveraging the `all-MiniLM-L6-v2` model) for incredibly fast, locally executed semantic matching.
- **`pandas`**: Handles robust I/O parsing and rapid manipulation of the unstructured client Excel files.
- **`PyTorch`**: Serves as the underlying tensor backend executing the Hugging Face model inferences.

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
git clone https://github.com/kshgrshrn/Semantic-GST-Schema-Standardization-Engine.git
cd Semantic-GST-Schema-Standardization-Engine

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

```bash
# Run the standardizer on the sample input file
python cli.py --input sample_data/sample_input.xlsx --output renamed.xlsx

# Run the benchmark to reproduce the metrics above (seed=42)
python -m gst_engine.evaluator
```

A sanitized demo input/output pair is in `sample_data/` if you want to see what the transformation looks like without needing the original files.

---

## Project Structure

```
gst_engine/
├── schema.py       # 61-field canonical GST schema — single source of truth
├── mapper.py       # SchemaMapper class: encodes headers, runs argmax similarity
├── trainer.py      # Fine-tuning script
├── evaluator.py    # Benchmark: baseline vs fine-tuned, seed=42
└── utils.py        # Excel IO, logging, config loading
cli.py              # CLI entrypoint: --input, --output, --config
config.yaml         # Model name, path, similarity threshold
sample_data/        # Sample input/output pair for demo
legacy/             # Original single-file scripts (archived)
```

---

## Architecture & Engineering Decisions

This project was initially prototyped as a monolithic script during the internship. It has since been refactored into a modular Python package to align with production engineering standards. Key architectural decisions include:

- **Separation of Concerns:** The model loading, inference logic, and canonical schema are strictly decoupled. The schema (`schema.py`) acts as a single source of truth, making it easy to adapt to new tax formats without altering the inference engine.
- **Stateful Mapper Instance:** By encapsulating the inference pipeline within a `SchemaMapper` class, the computationally expensive tasks of loading the Hugging Face model and encoding the 61 canonical headers are performed only once upon initialization, rather than repeatedly.
- **CLI Interface:** A dedicated entrypoint (`cli.py`) handles argument parsing, configuration injection, and routing. This allows the tool to be integrated cleanly into data engineering pipelines without polluting the core logic.

---

## Python API Usage

You can also use the engine as an importable module in your own Python pipelines:

```python
import pandas as pd
from gst_engine.mapper import SchemaMapper

# Load client data
df = pd.read_excel("client_vendor_data.xlsx")

# Initialize mapper
mapper = SchemaMapper(model_name="all-MiniLM-L6-v2", threshold=0.5)

# Map headers & print confidences
renamed_df, mappings = mapper.rename_dataframe(df)
for canonical, (original, score) in mappings.items():
    print(f"{canonical} <- {original} (score: {score:.2f})")
```

---

## Project History & Roadmap

### V1: The Internship Prototype (Monolithic)

The initial version built during the EY internship was a single monolithic script (`standardize.py`). It loaded the model, defined the schema, and ran the inference logic sequentially. While it proved the core NLP concept, it lacked modularity, handled configuration via hardcoding, and ran training on import.

### V2: Architectural Refactor (Current)

Post-internship, the project was restructured into a production-ready Python package (`gst_engine/`). Key improvements include:

- **Decoupling:** Schema, mapping logic, and training separated into distinct modules.
- **Class-Based API:** The `SchemaMapper` class ensures models and embeddings are loaded into memory exactly once.
- **CLI Implementation:** Argument parsing and YAML configuration support added via `cli.py`.

### V3: Upcoming Infrastructure Upgrades (Addressing Issues)

The immediate roadmap focuses on addressing several core issues and elevating the system from a strong proof-of-concept to production-grade ML infrastructure:

- **Fix Inference Collision Bug [High Priority]:** Refactor `SchemaMapper` to key results by input columns rather than canonical headers, preventing silent overwrites when multiple columns map to the same target.
- **Held-Out Evaluation Set:** Replace the current synthetic, rule-based benchmark with a hand-annotated evaluation set (300+ real-world variations) to measure true generalization and produce a confusion matrix.
- **Hybrid Retrieval Pipeline:** Implement a two-stage architecture: BM25 for initial lexical retrieval (handling extreme abbreviations like "Inv No") followed by a Cross-Encoder for semantic reranking.
- **Hard Negative Fine-Tuning:** Transition from standard cosine loss to `MultipleNegativesRankingLoss` (MNRL), training on explicitly constructed hard negatives (e.g., distinguishing "IGST", "CGST", and "SGST").
- **Batch Inference & FAISS:** Optimize the inference loop by batching `model.encode()` calls and introducing FAISS for fast, scalable vector search.
- **Audit Logging (JSONL):** Output a machine-readable log of automated decisions vs. flagged elements requiring human review.
