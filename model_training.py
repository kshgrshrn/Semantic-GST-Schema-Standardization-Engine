import pandas as pd
import numpy as np
from datasets import Dataset

from sentence_transformers import SentenceTransformer as st
from sentence_transformers import SentenceTransformerTrainer, losses
from sentence_transformers.util import cos_sim


# Load and train the model

# Load pre-trained model
model = st("all-MiniLM-L6-v2")


# Load and prepare training data
df_train = pd.read_excel("trainingdata.xlsx")
df_train.dropna(inplace=True)

train_dataset = Dataset.from_pandas(df_train)


# Initialize trainer with cosine similarity loss
trainer = SentenceTransformerTrainer(
    model=model,
    train_dataset=train_dataset,
    loss=losses.CosineSimilarityLoss(model)
)

# Train the model
trainer.train()

# Save the trained model
model.save("semantic_renamer_model_v2")
