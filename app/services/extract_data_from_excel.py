from typing import Dict
from io import BytesIO
import pandas as pd
from fastapi import UploadFile, HTTPException

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
