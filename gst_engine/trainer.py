"""Model training entrypoint for GST schema mapper."""

from __future__ import annotations

import argparse

import pandas as pd
from datasets import Dataset
from sentence_transformers import SentenceTransformer
from sentence_transformers import SentenceTransformerTrainer, losses
from sentence_transformers.training_args import SentenceTransformerTrainingArguments


def train_model(
    training_file: str = "trainingdata.xlsx",
    model_name: str = "all-MiniLM-L6-v2",
    output_path: str = "semantic_renamer_model_v2",
    epochs: int = 3,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
    warmup_ratio: float = 0.1,
    loss_type: str = "mnrl",
) -> None:
    """Fine-tune a sentence transformer for GST header matching.

    Parameters
    ----------
    training_file:
        Excel file with training pairs.  For ``mnrl`` loss the file must
        have columns ``anchor`` and ``positive``.  For ``cosine`` loss it
        must have ``sentence1``, ``sentence2``, and a float ``label``.
    loss_type:
        ``"mnrl"`` for MultipleNegativesRankingLoss (recommended for
        retrieval tasks — uses in-batch negatives so no explicit negative
        column is needed).  ``"cosine"`` for the original
        CosineSimilarityLoss.
    """
    model = SentenceTransformer(model_name)

    df_train = pd.read_excel(training_file)
    df_train.dropna(inplace=True)
    train_dataset = Dataset.from_pandas(df_train)

    if loss_type == "mnrl":
        loss = losses.MultipleNegativesRankingLoss(model)
    elif loss_type == "cosine":
        loss = losses.CosineSimilarityLoss(model)
    else:
        raise ValueError(f"Unknown loss type: {loss_type!r}. Use 'mnrl' or 'cosine'.")

    training_args = SentenceTransformerTrainingArguments(
        output_dir=output_path,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        learning_rate=learning_rate,
        warmup_ratio=warmup_ratio,
    )

    trainer = SentenceTransformerTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        loss=loss,
    )
    trainer.train()

    model.save(output_path)
    print(f"Model saved to {output_path}")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fine-tune sentence transformer for GST schema matching")
    p.add_argument("--training-file", default="trainingdata.xlsx", help="Path to training data Excel")
    p.add_argument("--model-name", default="all-MiniLM-L6-v2", help="Base model name")
    p.add_argument("--output", default="semantic_renamer_model_v2", help="Output directory")
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--lr", type=float, default=2e-5, help="Learning rate")
    p.add_argument("--warmup-ratio", type=float, default=0.1)
    p.add_argument("--loss", choices=["mnrl", "cosine"], default="mnrl", help="Loss function")
    return p


if __name__ == "__main__":
    args = _build_parser().parse_args()
    train_model(
        training_file=args.training_file,
        model_name=args.model_name,
        output_path=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        warmup_ratio=args.warmup_ratio,
        loss_type=args.loss,
    )
