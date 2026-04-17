"""
This script performs intelligent column header mapping and renaming using semantic similarity.

What it does:
1. Loads a base sentence transformer model.
2. Trains the model on a custom dataset to capture domain-specific semantics.
3. Compares column names from a target Excel file (`sample_file.xlsx`) to a predefined list of standard headers (`s1`).
4. Uses cosine similarity to determine the best matching header for each column.
5. Renames the columns in the file if similarity > 0.5 and saves it as `renamed.xlsx`.

For the frontend dev:
- You'll take an uploaded Excel file and send it to the backend.
- The backend returns a new Excel file with standardized column headers.
- Ensure file naming and path handling is robust when connecting to the UI.

The inference(s1, s2, model, dict) function and rename(file, dict) will be the functions used in case of a file upload.

Input file: sample_file.xlsx
Output file: renamed.xlsx (with renamed headers)
"""

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


# Define inference logic

def inference(s1, s2, model, dict_sim):
    """
    Compute cosine similarity between predefined headers (s1) and target columns (s2).
    Store matches and similarity scores in dict.
    """
    for i in s2:
        idx = s2.index(i)
        print(f'\n{s1[idx]} similarities\n')
        if pd.notna(i):
            cs = cos_sim(model.encode(s1[idx]), model.encode(i)).item()
            dict_sim[s1[idx]] = (i, cs)
            print(f'{s1[idx]}, {i} {cs}')
        else:
            continue


# List of standard headers

s1 = [
    "SourceIdentifier", "SourceFileName", "GLAccountCode", "Division", "SubDivision", "ProfitCentre1", "ProfitCentre2", "PlantCode",
    "ReturnPeriod", "RecipientGSTIN", "DocumentType", "SupplyType", "DocumentNumber", "DocumentDate", "OriginalDocumentNumber",
    "OriginalDocumentDate", "CRDRPreGST", "LineNumber", "SupplierGSTIN", "OriginalSupplierGSTIN", "SupplierName", "SupplierCode",
    "POS", "PortCode", "BillOfEntry", "BillOfEntryDate", "CIFValue", "CustomDuty", "HSNorSAC", "ItemCode", "ItemDescriptiion",
    "CategoryOfItem", "UnitOfMeasurement", "Quantity", "TaxableValue", "IntegratedTaxRate", "IntegratedTaxAmount",
    "CentralTaxRate", "CentralTaxAmount", "StateUTTaxRate", "StateUTTaxAmount", "CessAmountAdvalorem", "CessRateSpecific",
    "CessAmountSpecific", "InvoiceValue", "ReverseChargeFlag", "EligibilityIndicator", "CommonSupplyIndicator", "AvailableIGST",
    "AvailableCGST", "AvailableSGST", "AvailableCess", "ITCReversalIdentifier", "ReasonForCreditDebitNote", "PurchaseVoucherNumber",
    "PurchaseVoucherDate", "PaymentVoucherNumber", "PaymentDate", "ContractNumber", "ContractDate", "ContractValue"
]


# Load input file

file = pd.read_excel("sample_file.xlsx")
s2 = file.columns.tolist()


# Prepare similarity dictionary

dict_sim = {}


# Run inference

inference(s1, s2, model, dict_sim)


# Define column renaming logic

def rename(file, dict_sim):
    """
    Rename columns in the dataframe based on similarity scores.
    Only rename if similarity score > 0.5.
    Save the renamed dataframe to 'renamed.xlsx'.
    """
    rename_map = {}

    for target_col in dict_sim:
        match_col, score = dict_sim[target_col]
        if score > 0.5:
            rename_map[match_col] = target_col

    file.rename(columns=rename_map, inplace=True)
    file.to_excel("renamed.xlsx", index=False)

    print("File columns renamed appropriately.")


# Apply renaming
rename(file, dict_sim)
