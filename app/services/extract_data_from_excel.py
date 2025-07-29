import json
from typing import Dict, Optional
from io import BytesIO
import pandas as pd
from fastapi import UploadFile, HTTPException
from app.utils.logger import logger
from docx import Document
import io

async def extract_fields_from_excel(file: UploadFile) -> Dict:
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))

        if df.empty:
            raise HTTPException(status_code=400, detail="Excel file is empty")

        # Extract first row as key-value pairs
        return df.iloc[0].to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing Excel: {str(e)}")
    



def safe_json_parse(data: Optional[str]) -> Optional[dict]:
    """
    Safely parses a JSON string into a Python dictionary.
    Returns None if input is empty, None, or invalid JSON.
    """
    try:
        if data and data.strip():
            return json.loads(data.strip())
        return None
    except Exception as e:
        logger.error(f"[ERROR] Failed to parse JSON: {data} | Error: {e}")
        return None
    


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])


