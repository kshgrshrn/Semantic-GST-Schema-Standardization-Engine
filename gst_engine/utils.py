"""Utility helpers for IO and logging."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

import pandas as pd
import yaml


def get_logger(name: str = "gst_engine") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    return logger


def read_excel(file_path: str) -> pd.DataFrame:
    return pd.read_excel(file_path)


def write_excel(dataframe: pd.DataFrame, file_path: str) -> None:
    dataframe.to_excel(file_path, index=False)


def load_config(config_path: str) -> Dict[str, Any]:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file) or {}

    return {
        "model_name": config.get("model_name", "all-MiniLM-L6-v2"),
        "model_path": config.get("model_path"),
        "threshold": float(config.get("threshold", 0.5)),
        "review_threshold": float(config.get("review_threshold", 0.55)),
    }
