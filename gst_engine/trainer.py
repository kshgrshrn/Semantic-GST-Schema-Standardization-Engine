"""Model training entrypoint for GST schema mapper."""

from __future__ import annotations

import pandas as pd
from datasets import Dataset
from sentence_transformers import SentenceTransformer
from sentence_transformers import SentenceTransformerTrainer, losses


def train_model(
    training_file: str = "trainingdata.xlsx",
    model_name: str = "all-MiniLM-L6-v2",
    output_path: str = "semantic_renamer_model_v2",
) -> None:
    model = SentenceTransformer(model_name)

    df_train = pd.read_excel(training_file)
    df_train.dropna(inplace=True)
    train_dataset = Dataset.from_pandas(df_train)

    trainer = SentenceTransformerTrainer(
        model=model,
        train_dataset=train_dataset,
        loss=losses.CosineSimilarityLoss(model),
    )
    trainer.train()

    model.save(output_path)


if __name__ == "__main__":
    train_model()
