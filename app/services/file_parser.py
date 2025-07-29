from fastapi import UploadFile
from typing import List
import pandas as pd
import io
from dateutil import parser


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
    

# async def parse_uploaded_files(files: List[UploadFile]):
#     parsed_output = []

#     for file in files:
#         content = await file.read()
#         # Placeholder parse logic
#         parsed_output.append({
#             "filename": file.filename,
#             "parsed_content": f"Mock parsed text from {file.filename}",
#             "size": len(content)
#         })

#     return parsed_output




def is_possible_date_column(label: str) -> bool:
    label_lower = label.lower()
    return any(keyword in label_lower for keyword in ["date", "departure", "transport", "document"])

def try_parse_date(value):
    try:
        parsed = parser.parse(str(value), dayfirst=True)  # Assume D/M/Y or natural format
        return parsed.date().isoformat()  # Convert to "YYYY-MM-DD"
    except Exception:
        return value  # Return as-is if not a valid date

def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if is_possible_date_column(col):
            df[col] = df[col].apply(try_parse_date)
    return df

async def parse_uploaded_files(files: List[UploadFile]) -> List[dict]:
    all_data = []

    for file in files:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        df.columns = [col.strip() for col in df.columns]  # Optional cleanup

        df = normalize_dates(df)

        data = df.to_dict(orient='records')
        all_data.extend(data)

    return all_data



