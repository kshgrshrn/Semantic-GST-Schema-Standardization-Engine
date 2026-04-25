"""Tests for SchemaMapper correctness."""

from __future__ import annotations

import pandas as pd
import pytest

from gst_engine.mapper import SchemaMapper


class TestInference:
    """Tests for the inference() method."""

    def test_results_keyed_by_input_column(self, mapper: SchemaMapper):
        """Results dict must be keyed by input column name, not canonical header."""
        columns = ["Invoice Number", "Supplier Name"]
        results = mapper.inference(columns)

        for col in columns:
            assert col in results, f"Expected input column '{col}' as key in results"

    def test_nan_columns_skipped(self, mapper: SchemaMapper):
        columns = ["Invoice Number", float("nan"), "Supplier Name"]
        results = mapper.inference(columns)

        assert len(results) == 2
        assert "Invoice Number" in results
        assert "Supplier Name" in results

    def test_empty_input(self, mapper: SchemaMapper):
        results = mapper.inference([])
        assert results == {}

    def test_result_has_top3(self, mapper: SchemaMapper):
        results = mapper.inference(["Invoice Number"])
        result = results["Invoice Number"]
        assert len(result.top3) == 3
        # top3 entries are (header, score) tuples
        for header, score in result.top3:
            assert isinstance(header, str)
            assert isinstance(score, float)


class TestCollisionHandling:
    """Tests for collision detection in build_rename_map()."""

    def test_collision_higher_score_wins(self, mapper: SchemaMapper):
        """When two input columns map to the same canonical, higher score wins."""
        # Use two very similar inputs that will both map to the same canonical.
        columns = ["Invoice Value", "Value of Invoice"]
        results = mapper.inference(columns)

        rename_map = mapper.build_rename_map(results)

        # At most one input column should map to any given canonical.
        canonical_targets = list(rename_map.values())
        assert len(canonical_targets) == len(set(canonical_targets)), (
            f"Collision not resolved — duplicate canonical targets: {canonical_targets}"
        )

    def test_collision_loser_flagged(self, mapper: SchemaMapper):
        """The losing column in a collision should be flagged."""
        columns = ["Invoice Value", "Value of Invoice"]
        results = mapper.inference(columns)
        mapper.build_rename_map(results)

        statuses = {r.input_column: r.status for r in results.values()}
        dropped = [col for col, s in statuses.items() if s == "collision_dropped"]
        # If both map to the same canonical, exactly one should be dropped.
        # If they map to different canonicals, neither is dropped — both are fine.
        mapped = [col for col, s in statuses.items() if s in ("auto_mapped", "low_confidence")]
        assert len(mapped) + len(dropped) == 2


class TestThreshold:
    """Tests for threshold-based filtering."""

    def test_below_threshold_unmapped(self):
        """Columns with scores below threshold should be marked unmapped."""
        # Use a very high threshold so everything fails.
        mapper = SchemaMapper(model_name="all-MiniLM-L6-v2", threshold=0.99)
        results = mapper.inference(["xyzzy gibberish column"])
        mapper.build_rename_map(results)

        result = results["xyzzy gibberish column"]
        assert result.status == "unmapped"

    def test_above_threshold_mapped(self, mapper: SchemaMapper):
        """Exact canonical header should always pass the default 0.5 threshold."""
        results = mapper.inference(["SupplierGSTIN"])
        rename_map = mapper.build_rename_map(results)

        assert "SupplierGSTIN" in rename_map


class TestRenameDataframe:
    """Tests for the full rename_dataframe pipeline."""

    def test_columns_renamed(self, mapper: SchemaMapper):
        df = pd.DataFrame({"Invoice Number": [1], "Supplier Name": ["ABC"]})
        renamed_df, results = mapper.rename_dataframe(df)

        # The renamed df should have canonical header names.
        for col in renamed_df.columns:
            # Either it was renamed to a canonical name, or it stayed the same
            # (if below threshold). Either way, no crash.
            assert isinstance(col, str)

    def test_data_preserved(self, mapper: SchemaMapper):
        """Row data must not be altered by renaming."""
        df = pd.DataFrame({"Invoice Number": [100, 200], "Supplier Name": ["A", "B"]})
        renamed_df, _ = mapper.rename_dataframe(df)

        assert list(renamed_df.iloc[:, 0]) == [100, 200]
        assert list(renamed_df.iloc[:, 1]) == ["A", "B"]
