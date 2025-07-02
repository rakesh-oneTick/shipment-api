import json
from typing import Union
from fastapi import UploadFile

# Placeholder OCR function
async def parse_document(file: UploadFile) -> dict:
    filename = file.filename.lower()

    # Simulated parsed values (In real case: extracted by OCR/LLM)
    if "invoice" in filename:
        return {
            "type": "invoice",
            "invoice_number": "INV-2024-001",
            "date": "2024-06-01",
            "amount": "₹15,000",
            "currency": "INR",
            "vendor": "ABC Traders"
        }

    elif "aadhar" in filename:
        return {
            "type": "aadhar",
            "name": "Ravi Kumar",
            "dob": "1985-03-12",
            "aadhar_number": "1234-5678-9012",
            "gender": "Male"
        }

    else:
        # Generic simulated result
        contents = await file.read()
        return {
            "type": "unknown",
            "filename": file.filename,
            "length": len(contents),
            "raw_text": contents.decode(errors='ignore')[:500]  # limit preview
        }