"""Schema mapping module based on cosine similarity."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from .schema import CANONICAL_HEADERS

logger = logging.getLogger(__name__)


@dataclass
class ColumnResult:
    """Mapping result for a single input column."""

    input_column: str
    top1: str
    top1_score: float
    top3: List[Tuple[str, float]]
    status: str = ""  # "auto_mapped", "low_confidence", "unmapped", "collision_dropped"

    def to_dict(self) -> dict:
        return {
            "input_column": self.input_column,
            "canonical_match": self.top1,
            "score": round(self.top1_score, 4),
            "status": self.status,
            "top3_candidates": [[h, round(s, 4)] for h, s in self.top3],
        }


# Public type alias for the results dict.
MappingResults = Dict[str, ColumnResult]


class SchemaMapper:
    """Maps input headers to canonical GST headers using semantic similarity."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        model_path: str | None = None,
        threshold: float = 0.35,
        review_threshold: float = 0.55,
    ) -> None:
        self.threshold = threshold
        self.review_threshold = review_threshold
        self.model = SentenceTransformer(model_path or model_name)
        # Encode canonical headers once and reuse for every incoming column.
        self._canonical_embeddings = self.model.encode(
            CANONICAL_HEADERS, show_progress_bar=False,
        )

    def inference(self, input_columns: list[object]) -> MappingResults:
        """Return best canonical match and score for each input column.

        Results are keyed by **input column name** (not canonical header)
        so that collisions are visible rather than silently overwritten.
        """
        results: MappingResults = {}

        # Filter out NaN columns and convert to strings.
        clean_columns = [str(c) for c in input_columns if not pd.isna(c)]
        if not clean_columns:
            return results

        # Batch encode all input columns in one call.
        query_embeddings = self.model.encode(
            clean_columns, show_progress_bar=False,
        )

        all_scores = cos_sim(query_embeddings, self._canonical_embeddings).cpu().numpy()

        for idx, col_text in enumerate(clean_columns):
            scores = all_scores[idx]
            ranked = np.argsort(scores)[::-1]

            top1_header = CANONICAL_HEADERS[ranked[0]]
            top1_score = float(scores[ranked[0]])
            top3 = [
                (CANONICAL_HEADERS[int(i)], float(scores[int(i)]))
                for i in ranked[:3]
            ]

            results[col_text] = ColumnResult(
                input_column=col_text,
                top1=top1_header,
                top1_score=top1_score,
                top3=top3,
            )

        return results

    def build_rename_map(self, results: MappingResults) -> Dict[str, str]:
        """Build a dataframe rename map with collision detection.

        When two input columns both map to the same canonical header,
        the column with the higher score wins.  The loser is logged and
        its status set to ``collision_dropped``.
        """
        # First pass: group by canonical target.
        canonical_to_inputs: Dict[str, List[ColumnResult]] = {}
        for result in results.values():
            if result.top1_score <= self.threshold:
                result.status = "unmapped"
                continue
            canonical_to_inputs.setdefault(result.top1, []).append(result)

        rename_map: Dict[str, str] = {}
        for canonical, contenders in canonical_to_inputs.items():
            # Sort descending by score — winner is first.
            contenders.sort(key=lambda r: r.top1_score, reverse=True)
            winner = contenders[0]

            if winner.top1_score >= self.review_threshold:
                winner.status = "auto_mapped"
            else:
                winner.status = "low_confidence"

            rename_map[winner.input_column] = canonical

            # Flag losers.
            for loser in contenders[1:]:
                loser.status = "collision_dropped"
                logger.warning(
                    "Collision: '%s' (score=%.4f) lost to '%s' (score=%.4f) "
                    "for canonical target '%s'",
                    loser.input_column, loser.top1_score,
                    winner.input_column, winner.top1_score,
                    canonical,
                )

        return rename_map

    def rename_dataframe(
        self, dataframe: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, MappingResults]:
        """Rename dataframe columns by semantic similarity and return results."""
        results = self.inference(dataframe.columns.tolist())
        rename_map = self.build_rename_map(results)
        renamed_df = dataframe.rename(columns=rename_map)
        return renamed_df, results

    def write_audit_log(self, results: MappingResults, path: str) -> None:
        """Write a JSONL audit log of all mapping decisions."""
        with open(path, "w", encoding="utf-8") as f:
            for result in results.values():
                f.write(json.dumps(result.to_dict()) + "\n")
        logger.info("Audit log written to %s", path)
