"""Schema mapping module based on cosine similarity."""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from .schema import CANONICAL_HEADERS


SimilarityDict = Dict[str, Tuple[str, float]]


class SchemaMapper:
    """Maps input headers to canonical GST headers using semantic similarity."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        model_path: str | None = None,
        threshold: float = 0.5,
    ) -> None:
        self.threshold = threshold
        self.model = SentenceTransformer(model_path or model_name)
        # Encode canonical headers once and reuse for every incoming column.
        self._canonical_embeddings = self.model.encode(CANONICAL_HEADERS)

    def inference(self, input_columns: Iterable[object]) -> SimilarityDict:
        """Return best canonical match and score for each input column."""
        similarities: SimilarityDict = {}

        for column in input_columns:
            if pd.isna(column):
                continue

            col_text = str(column)
            query_embedding = self.model.encode(col_text)
            scores = cos_sim(query_embedding, self._canonical_embeddings)[0].cpu().numpy()

            best_idx = int(np.argmax(scores))
            best_header = CANONICAL_HEADERS[best_idx]
            best_score = float(scores[best_idx])
            similarities[best_header] = (col_text, best_score)

        return similarities

    def build_rename_map(self, similarities: SimilarityDict) -> Dict[str, str]:
        """Build a dataframe rename map using the configured threshold."""
        rename_map: Dict[str, str] = {}
        for canonical_header, (matched_input_col, score) in similarities.items():
            if score > self.threshold:
                rename_map[matched_input_col] = canonical_header
        return rename_map

    def rename_dataframe(self, dataframe: pd.DataFrame) -> Tuple[pd.DataFrame, SimilarityDict]:
        """Rename dataframe columns by semantic similarity and return results."""
        similarities = self.inference(dataframe.columns.tolist())
        rename_map = self.build_rename_map(similarities)
        renamed_df = dataframe.rename(columns=rename_map)
        return renamed_df, similarities
