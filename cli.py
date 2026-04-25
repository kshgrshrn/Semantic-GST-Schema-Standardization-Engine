"""Command-line entrypoint for GST schema standardization."""

from __future__ import annotations

import argparse

from gst_engine.mapper import SchemaMapper
from gst_engine.utils import get_logger, load_config, read_excel, write_excel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Semantic GST header standardization")
    parser.add_argument("--input", required=True, help="Path to input Excel file")
    parser.add_argument("--output", default="renamed.xlsx", help="Path to output Excel file")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config")
    parser.add_argument("--audit", default=None, help="Path to write JSONL audit log")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    logger = get_logger()
    config = load_config(args.config)

    mapper = SchemaMapper(
        model_name=config["model_name"],
        model_path=config["model_path"],
        threshold=config["threshold"],
    )

    dataframe = read_excel(args.input)
    renamed_df, results = mapper.rename_dataframe(dataframe)
    write_excel(renamed_df, args.output)

    logger.info("Column standardization complete. Output written to %s", args.output)

    # Report all mapping decisions.
    unmapped = []
    for col_name, result in results.items():
        logger.info(
            "%s -> %s (score=%.4f, status=%s)",
            result.input_column, result.top1, result.top1_score, result.status,
        )
        if result.status in ("unmapped", "collision_dropped"):
            unmapped.append(result)

    if unmapped:
        logger.warning(
            "%d column(s) were NOT mapped: %s",
            len(unmapped),
            [r.input_column for r in unmapped],
        )

    if args.audit:
        mapper.write_audit_log(results, args.audit)


if __name__ == "__main__":
    main()
