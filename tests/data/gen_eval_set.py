import json, os

ENTRIES = [
    # ── SourceIdentifier ─────────────────────────────────────────────────
    ("Source ID", "SourceIdentifier", "abbreviation"),
    ("Src Identifier", "SourceIdentifier", "abbreviation"),
    ("source identifier", "SourceIdentifier", "lowercase"),
    ("SOURCE IDENTIFIER", "SourceIdentifier", "allcaps"),
    ("Src Id", "SourceIdentifier", "abbreviation"),
    # ── SourceFileName ────────────────────────────────────────────────────
    ("Source File", "SourceFileName", "truncation"),
    ("File Name", "SourceFileName", "reorder"),
    ("Src File Name", "SourceFileName", "abbreviation"),
    ("source file name", "SourceFileName", "lowercase"),
    ("SOURCE FILE NAME", "SourceFileName", "allcaps"),
    # ── GLAccountCode ─────────────────────────────────────────────────────
    ("GL Code", "GLAccountCode", "abbreviation"),
    ("G/L Account", "GLAccountCode", "reorder"),
    ("GL Acc Code", "GLAccountCode", "abbreviation"),
    ("General Ledger Code", "GLAccountCode", "expansion"),
    ("gl account code", "GLAccountCode", "lowercase"),
    # ── Division ──────────────────────────────────────────────────────────
    ("Div", "Division", "abbreviation"),
    ("Business Division", "Division", "expansion"),
    ("division", "Division", "lowercase"),
    ("DIVISION", "Division", "allcaps"),
    # ── SubDivision ───────────────────────────────────────────────────────
    ("Sub Div", "SubDivision", "abbreviation"),
    ("Sub-Division", "SubDivision", "hyphen"),
    ("subdivision", "SubDivision", "lowercase"),
    ("SUB DIVISION", "SubDivision", "allcaps"),
    # ── ProfitCentre1 ─────────────────────────────────────────────────────
    ("PC1", "ProfitCentre1", "abbreviation"),
    ("Profit Centre 1", "ProfitCentre1", "spaced"),
    ("Profit Center 1", "ProfitCentre1", "us_spelling"),
    ("profit centre1", "ProfitCentre1", "lowercase"),
    # ── ProfitCentre2 ─────────────────────────────────────────────────────
    ("PC2", "ProfitCentre2", "abbreviation"),
    ("Profit Centre 2", "ProfitCentre2", "spaced"),
    ("Profit Center 2", "ProfitCentre2", "us_spelling"),
    ("profit centre2", "ProfitCentre2", "lowercase"),
    # ── PlantCode ─────────────────────────────────────────────────────────
    ("Plant", "PlantCode", "truncation"),
    ("Plant No", "PlantCode", "abbreviation"),
    ("Plant Cd", "PlantCode", "abbreviation"),
    ("plant code", "PlantCode", "lowercase"),
    ("PLANT CODE", "PlantCode", "allcaps"),
    # ── ReturnPeriod ──────────────────────────────────────────────────────
    ("Return Period", "ReturnPeriod", "spaced"),
    ("Ret Period", "ReturnPeriod", "abbreviation"),
    ("Filing Period", "ReturnPeriod", "synonym"),
    ("return period", "ReturnPeriod", "lowercase"),
    ("RETURN PERIOD", "ReturnPeriod", "allcaps"),
    # ── RecipientGSTIN ────────────────────────────────────────────────────
    ("Recipient GST No", "RecipientGSTIN", "abbreviation"),
    ("Buyer GSTIN", "RecipientGSTIN", "synonym"),
    ("Recipient Tax ID", "RecipientGSTIN", "synonym"),
    ("recipient gstin", "RecipientGSTIN", "lowercase"),
    ("RECIPIENT GSTIN", "RecipientGSTIN", "allcaps"),
    # ── DocumentType ──────────────────────────────────────────────────────
    ("Doc Type", "DocumentType", "abbreviation"),
    ("Doct Type", "DocumentType", "typo"),
    ("Document Typ", "DocumentType", "truncation"),
    ("document type", "DocumentType", "lowercase"),
    ("DOC TYPE", "DocumentType", "allcaps"),
    # ── SupplyType ────────────────────────────────────────────────────────
    ("Supply Typ", "SupplyType", "truncation"),
    ("Sply Type", "SupplyType", "abbreviation"),
    ("Type of Supply", "SupplyType", "reorder"),
    ("supply type", "SupplyType", "lowercase"),
    ("SUPPLY TYPE", "SupplyType", "allcaps"),
    # ── DocumentNumber ────────────────────────────────────────────────────
    ("Doc No", "DocumentNumber", "abbreviation"),
    ("Document No", "DocumentNumber", "abbreviation"),
    ("Voucher Number", "DocumentNumber", "synonym"),
    ("Doc Num", "DocumentNumber", "abbreviation"),
    ("document number", "DocumentNumber", "lowercase"),
    # ── DocumentDate ──────────────────────────────────────────────────────
    ("Doc Date", "DocumentDate", "abbreviation"),
    ("Document Dt", "DocumentDate", "abbreviation"),
    ("Date of Document", "DocumentDate", "reorder"),
    ("document date", "DocumentDate", "lowercase"),
    ("DOC DATE", "DocumentDate", "allcaps"),
    # ── OriginalDocumentNumber ────────────────────────────────────────────
    ("Orig Doc No", "OriginalDocumentNumber", "abbreviation"),
    ("Original Doc Num", "OriginalDocumentNumber", "abbreviation"),
    ("Org Doc No", "OriginalDocumentNumber", "abbreviation"),
    ("original document number", "OriginalDocumentNumber", "lowercase"),
    # ── OriginalDocumentDate ──────────────────────────────────────────────
    ("Orig Doc Date", "OriginalDocumentDate", "abbreviation"),
    ("Original Doc Dt", "OriginalDocumentDate", "abbreviation"),
    ("Org Doc Date", "OriginalDocumentDate", "abbreviation"),
    ("original document date", "OriginalDocumentDate", "lowercase"),
    # ── CRDRPreGST ────────────────────────────────────────────────────────
    ("CR DR Pre GST", "CRDRPreGST", "spaced"),
    ("Credit Debit Pre GST", "CRDRPreGST", "expansion"),
    ("Pre GST CRDR", "CRDRPreGST", "reorder"),
    ("crdr pre gst", "CRDRPreGST", "lowercase"),
    # ── LineNumber ────────────────────────────────────────────────────────
    ("Line No", "LineNumber", "abbreviation"),
    ("Sr No", "LineNumber", "synonym"),
    ("Serial Number", "LineNumber", "synonym"),
    ("line number", "LineNumber", "lowercase"),
    ("LINE NO", "LineNumber", "allcaps"),
    # ── SupplierGSTIN ─────────────────────────────────────────────────────
    ("Supplier GST No", "SupplierGSTIN", "abbreviation"),
    ("Vendor GSTIN", "SupplierGSTIN", "synonym"),
    ("Seller GST ID", "SupplierGSTIN", "synonym"),
    ("supplier gstin", "SupplierGSTIN", "lowercase"),
    ("SUPPLIER GSTIN", "SupplierGSTIN", "allcaps"),
    # Hard negatives — near IGST/CGST/SGST confusion zone
    ("Supplier Tax No", "SupplierGSTIN", "synonym"),
    # ── OriginalSupplierGSTIN ─────────────────────────────────────────────
    ("Orig Supplier GSTIN", "OriginalSupplierGSTIN", "abbreviation"),
    ("Original Vendor GST No", "OriginalSupplierGSTIN", "synonym"),
    ("Org Supplier GST ID", "OriginalSupplierGSTIN", "abbreviation"),
    ("original supplier gstin", "OriginalSupplierGSTIN", "lowercase"),
    # ── SupplierName ──────────────────────────────────────────────────────
    ("Supplier Name", "SupplierName", "spaced"),
    ("Vendor Name", "SupplierName", "synonym"),
    ("Party Name", "SupplierName", "synonym"),
    ("Seller Name", "SupplierName", "synonym"),
    ("supplier name", "SupplierName", "lowercase"),
    ("Name of Supplier", "SupplierName", "reorder"),
    # ── SupplierCode ──────────────────────────────────────────────────────
    ("Supplier Code", "SupplierCode", "spaced"),
    ("Vendor Code", "SupplierCode", "synonym"),
    ("Party Code", "SupplierCode", "synonym"),
    ("Supp Cd", "SupplierCode", "abbreviation"),
    ("supplier code", "SupplierCode", "lowercase"),
    # ── POS ───────────────────────────────────────────────────────────────
    ("Place of Supply", "POS", "expansion"),
    ("Place Of Sply", "POS", "abbreviation"),
    ("State of Supply", "POS", "synonym"),
    ("pos", "POS", "lowercase"),
    ("P.O.S.", "POS", "punctuation"),
    # ── PortCode ──────────────────────────────────────────────────────────
    ("Port Code", "PortCode", "spaced"),
    ("Port Cd", "PortCode", "abbreviation"),
    ("port code", "PortCode", "lowercase"),
    ("PORT CODE", "PortCode", "allcaps"),
    # ── BillOfEntry ───────────────────────────────────────────────────────
    ("Bill of Entry", "BillOfEntry", "spaced"),
    ("Bil of Entr", "BillOfEntry", "truncation"),
    ("BOE", "BillOfEntry", "acronym"),
    ("Bill Of Entry No", "BillOfEntry", "extra_word"),
    ("bill of entry", "BillOfEntry", "lowercase"),
    # ── BillOfEntryDate ───────────────────────────────────────────────────
    ("BOE Date", "BillOfEntryDate", "acronym"),
    ("Bill of Entry Date", "BillOfEntryDate", "spaced"),
    ("Bil Entr Dt", "BillOfEntryDate", "abbreviation"),
    ("bill of entry date", "BillOfEntryDate", "lowercase"),
    # ── CIFValue ──────────────────────────────────────────────────────────
    ("CIF Value", "CIFValue", "spaced"),
    ("CIF Val", "CIFValue", "abbreviation"),
    ("Cost Insurance Freight", "CIFValue", "expansion"),
    ("cif value", "CIFValue", "lowercase"),
    # ── CustomDuty ────────────────────────────────────────────────────────
    ("Custom Duty", "CustomDuty", "spaced"),
    ("Customs Duty", "CustomDuty", "plural"),
    ("Import Duty", "CustomDuty", "synonym"),
    ("Cust Duty", "CustomDuty", "abbreviation"),
    ("custom duty", "CustomDuty", "lowercase"),
    # ── HSNorSAC ──────────────────────────────────────────────────────────
    ("HSN Code", "HSNorSAC", "partial"),
    ("SAC Code", "HSNorSAC", "partial"),
    ("HSN/SAC", "HSNorSAC", "slash"),
    ("HSN or SAC", "HSNorSAC", "spaced"),
    ("hsn code", "HSNorSAC", "lowercase"),
    ("HSN SAC Code", "HSNorSAC", "spaced"),
    # ── ItemCode ──────────────────────────────────────────────────────────
    ("Item Code", "ItemCode", "spaced"),
    ("Product Code", "ItemCode", "synonym"),
    ("SKU", "ItemCode", "acronym"),
    ("Item Cd", "ItemCode", "abbreviation"),
    ("item code", "ItemCode", "lowercase"),
    # ── ItemDescriptiion ──────────────────────────────────────────────────
    ("Item Description", "ItemDescriptiion", "corrected_typo"),
    ("Item Desc", "ItemDescriptiion", "abbreviation"),
    ("Product Description", "ItemDescriptiion", "synonym"),
    ("Goods Description", "ItemDescriptiion", "synonym"),
    ("item description", "ItemDescriptiion", "lowercase"),
    # ── CategoryOfItem ────────────────────────────────────────────────────
    ("Item Category", "CategoryOfItem", "reorder"),
    ("Category", "CategoryOfItem", "truncation"),
    ("Product Category", "CategoryOfItem", "synonym"),
    ("category of item", "CategoryOfItem", "lowercase"),
    # ── UnitOfMeasurement ─────────────────────────────────────────────────
    ("UOM", "UnitOfMeasurement", "acronym"),
    ("Unit", "UnitOfMeasurement", "truncation"),
    ("Unit of Measure", "UnitOfMeasurement", "truncation"),
    ("Uom Code", "UnitOfMeasurement", "acronym"),
    ("unit of measurement", "UnitOfMeasurement", "lowercase"),
    # ── Quantity ──────────────────────────────────────────────────────────
    ("Qty", "Quantity", "abbreviation"),
    ("Qnty", "Quantity", "abbreviation"),
    ("Units", "Quantity", "synonym"),
    ("quantity", "Quantity", "lowercase"),
    ("QUANTITY", "Quantity", "allcaps"),
    # ── TaxableValue ──────────────────────────────────────────────────────
    ("Taxable Amt", "TaxableValue", "abbreviation"),
    ("Taxable Amount", "TaxableValue", "synonym"),
    ("Assessable Value", "TaxableValue", "synonym"),
    ("Tax Base", "TaxableValue", "synonym"),
    ("taxable value", "TaxableValue", "lowercase"),
    # ── IntegratedTaxRate ─────────────────────────────────────────────────
    ("IGST Rate", "IntegratedTaxRate", "abbreviation"),
    ("IGST %", "IntegratedTaxRate", "abbreviation"),
    ("Integrated Tax Rate", "IntegratedTaxRate", "spaced"),
    ("igst rate", "IntegratedTaxRate", "lowercase"),
    ("IGST Pct", "IntegratedTaxRate", "abbreviation"),
    # ── IntegratedTaxAmount ───────────────────────────────────────────────
    ("IGST Amt", "IntegratedTaxAmount", "abbreviation"),
    ("IGST Amount", "IntegratedTaxAmount", "abbreviation"),
    ("Integrated Tax Amt", "IntegratedTaxAmount", "abbreviation"),
    ("igst amount", "IntegratedTaxAmount", "lowercase"),
    ("IGST", "IntegratedTaxAmount", "acronym"),
    # Hard negative — must NOT map to CentralTaxAmount or StateUTTaxAmount
    ("IGST Value", "IntegratedTaxAmount", "synonym"),
    # ── CentralTaxRate ────────────────────────────────────────────────────
    ("CGST Rate", "CentralTaxRate", "abbreviation"),
    ("CGST %", "CentralTaxRate", "abbreviation"),
    ("Central Tax Rate", "CentralTaxRate", "spaced"),
    ("cgst rate", "CentralTaxRate", "lowercase"),
    ("CGST Pct", "CentralTaxRate", "abbreviation"),
    # ── CentralTaxAmount ──────────────────────────────────────────────────
    ("CGST Amt", "CentralTaxAmount", "abbreviation"),
    ("CGST Amount", "CentralTaxAmount", "abbreviation"),
    ("Central Tax Amt", "CentralTaxAmount", "abbreviation"),
    ("cgst amount", "CentralTaxAmount", "lowercase"),
    ("CGST", "CentralTaxAmount", "acronym"),
    ("CGST Value", "CentralTaxAmount", "synonym"),
    # ── StateUTTaxRate ────────────────────────────────────────────────────
    ("SGST Rate", "StateUTTaxRate", "abbreviation"),
    ("UTGST Rate", "StateUTTaxRate", "abbreviation"),
    ("SGST %", "StateUTTaxRate", "abbreviation"),
    ("State Tax Rate", "StateUTTaxRate", "synonym"),
    ("sgst rate", "StateUTTaxRate", "lowercase"),
    # ── StateUTTaxAmount ──────────────────────────────────────────────────
    ("SGST Amt", "StateUTTaxAmount", "abbreviation"),
    ("SGST Amount", "StateUTTaxAmount", "abbreviation"),
    ("UTGST Amt", "StateUTTaxAmount", "abbreviation"),
    ("sgst amount", "StateUTTaxAmount", "lowercase"),
    ("SGST", "StateUTTaxAmount", "acronym"),
    ("SGST Value", "StateUTTaxAmount", "synonym"),
    # ── CessAmountAdvalorem ───────────────────────────────────────────────
    ("Cess Amt", "CessAmountAdvalorem", "abbreviation"),
    ("Cess Amount Ad Valorem", "CessAmountAdvalorem", "spaced"),
    ("Ad Valorem Cess", "CessAmountAdvalorem", "reorder"),
    ("cess amount advalorem", "CessAmountAdvalorem", "lowercase"),
    ("Cess (Ad Valorem)", "CessAmountAdvalorem", "punctuation"),
    # ── CessRateSpecific ──────────────────────────────────────────────────
    ("Cess Rate", "CessRateSpecific", "truncation"),
    ("Specific Cess Rate", "CessRateSpecific", "reorder"),
    ("cess rate specific", "CessRateSpecific", "lowercase"),
    ("CESS RATE SPECIFIC", "CessRateSpecific", "allcaps"),
    # ── CessAmountSpecific ────────────────────────────────────────────────
    ("Specific Cess Amt", "CessAmountSpecific", "abbreviation"),
    ("Cess Specific Amt", "CessAmountSpecific", "reorder"),
    ("cess amount specific", "CessAmountSpecific", "lowercase"),
    # ── InvoiceValue ──────────────────────────────────────────────────────
    ("Invoice Amt", "InvoiceValue", "abbreviation"),
    ("Invoice Amount", "InvoiceValue", "synonym"),
    ("Inv Value", "InvoiceValue", "abbreviation"),
    ("Inv Val", "InvoiceValue", "abbreviation"),
    ("invoice value", "InvoiceValue", "lowercase"),
    ("Value of Invoice", "InvoiceValue", "reorder"),
    ("Total Invoice Value", "InvoiceValue", "extra_word"),
    # ── ReverseChargeFlag ─────────────────────────────────────────────────
    ("Reverse Charge", "ReverseChargeFlag", "truncation"),
    ("RCM Flag", "ReverseChargeFlag", "abbreviation"),
    ("Reverse Charge Applicable", "ReverseChargeFlag", "expansion"),
    ("reverse charge flag", "ReverseChargeFlag", "lowercase"),
    ("RC Flag", "ReverseChargeFlag", "abbreviation"),
    # ── EligibilityIndicator ──────────────────────────────────────────────
    ("Eligibility", "EligibilityIndicator", "truncation"),
    ("ITC Eligible", "EligibilityIndicator", "synonym"),
    ("Eligibility Flag", "EligibilityIndicator", "synonym"),
    ("eligibility indicator", "EligibilityIndicator", "lowercase"),
    # ── CommonSupplyIndicator ─────────────────────────────────────────────
    ("Common Supply", "CommonSupplyIndicator", "truncation"),
    ("Common Supply Flag", "CommonSupplyIndicator", "synonym"),
    ("common supply indicator", "CommonSupplyIndicator", "lowercase"),
    # ── AvailableIGST ─────────────────────────────────────────────────────
    ("Avail IGST", "AvailableIGST", "abbreviation"),
    ("Available IGST Amt", "AvailableIGST", "extra_word"),
    ("ITC IGST", "AvailableIGST", "synonym"),
    ("available igst", "AvailableIGST", "lowercase"),
    ("AVAIL IGST", "AvailableIGST", "allcaps"),
    # ── AvailableCGST ─────────────────────────────────────────────────────
    ("Avail CGST", "AvailableCGST", "abbreviation"),
    ("Available CGST Amt", "AvailableCGST", "extra_word"),
    ("ITC CGST", "AvailableCGST", "synonym"),
    ("available cgst", "AvailableCGST", "lowercase"),
    # ── AvailableSGST ─────────────────────────────────────────────────────
    ("Avail SGST", "AvailableSGST", "abbreviation"),
    ("Available SGST Amt", "AvailableSGST", "extra_word"),
    ("ITC SGST", "AvailableSGST", "synonym"),
    ("available sgst", "AvailableSGST", "lowercase"),
    # ── AvailableCess ─────────────────────────────────────────────────────
    ("Avail Cess", "AvailableCess", "abbreviation"),
    ("Available Cess Amt", "AvailableCess", "extra_word"),
    ("ITC Cess", "AvailableCess", "synonym"),
    ("available cess", "AvailableCess", "lowercase"),
    # ── ITCReversalIdentifier ─────────────────────────────────────────────
    ("ITC Reversal", "ITCReversalIdentifier", "truncation"),
    ("ITC Rev ID", "ITCReversalIdentifier", "abbreviation"),
    ("ITC Reversal Flag", "ITCReversalIdentifier", "synonym"),
    ("itc reversal identifier", "ITCReversalIdentifier", "lowercase"),
    # ── ReasonForCreditDebitNote ──────────────────────────────────────────
    ("Reason for CDN", "ReasonForCreditDebitNote", "abbreviation"),
    ("Credit Debit Note Reason", "ReasonForCreditDebitNote", "reorder"),
    ("CDN Reason", "ReasonForCreditDebitNote", "abbreviation"),
    ("reason for credit debit note", "ReasonForCreditDebitNote", "lowercase"),
    ("Reason (CR/DR Note)", "ReasonForCreditDebitNote", "punctuation"),
    # ── PurchaseVoucherNumber ─────────────────────────────────────────────
    ("Purchase Voucher No", "PurchaseVoucherNumber", "abbreviation"),
    ("PV No", "PurchaseVoucherNumber", "abbreviation"),
    ("Purchase Voucher Num", "PurchaseVoucherNumber", "abbreviation"),
    ("purchase voucher number", "PurchaseVoucherNumber", "lowercase"),
    # ── PurchaseVoucherDate ───────────────────────────────────────────────
    ("Purchase Voucher Date", "PurchaseVoucherDate", "spaced"),
    ("PV Date", "PurchaseVoucherDate", "abbreviation"),
    ("Purchase Voucher Dt", "PurchaseVoucherDate", "abbreviation"),
    ("purchase voucher date", "PurchaseVoucherDate", "lowercase"),
    # ── PaymentVoucherNumber ──────────────────────────────────────────────
    ("Payment Voucher No", "PaymentVoucherNumber", "abbreviation"),
    ("Pay Voucher No", "PaymentVoucherNumber", "abbreviation"),
    ("Payment Vch No", "PaymentVoucherNumber", "abbreviation"),
    ("payment voucher number", "PaymentVoucherNumber", "lowercase"),
    # ── PaymentDate ───────────────────────────────────────────────────────
    ("Payment Date", "PaymentDate", "spaced"),
    ("Pay Date", "PaymentDate", "abbreviation"),
    ("Date of Payment", "PaymentDate", "reorder"),
    ("payment date", "PaymentDate", "lowercase"),
    # ── ContractNumber ────────────────────────────────────────────────────
    ("Contract No", "ContractNumber", "abbreviation"),
    ("Agreement No", "ContractNumber", "synonym"),
    ("Contract Num", "ContractNumber", "abbreviation"),
    ("contract number", "ContractNumber", "lowercase"),
    # ── ContractDate ──────────────────────────────────────────────────────
    ("Contract Date", "ContractDate", "spaced"),
    ("Contract Dt", "ContractDate", "abbreviation"),
    ("Date of Contract", "ContractDate", "reorder"),
    ("contract date", "ContractDate", "lowercase"),
    # ── ContractValue ─────────────────────────────────────────────────────
    ("Contract Value", "ContractValue", "spaced"),
    ("Contract Amt", "ContractValue", "abbreviation"),
    ("Agreement Value", "ContractValue", "synonym"),
    ("contract value", "ContractValue", "lowercase"),
    # ── Excel artifacts / real-world chaos ────────────────────────────────
    ("Unnamed: 3", "SourceIdentifier", "excel_artifact"),
    ("Column1", "SourceIdentifier", "excel_artifact"),
    ("Sheet1", "SourceFileName", "excel_artifact"),
]

out = os.path.join(os.path.dirname(__file__), "eval_set.jsonl")
with open(out, "w", encoding="utf-8") as f:
    for noisy, canonical, category in ENTRIES:
        f.write(json.dumps({"noisy": noisy, "canonical": canonical, "category": category}) + "\n")

print(f"Written {len(ENTRIES)} entries to {out}")
