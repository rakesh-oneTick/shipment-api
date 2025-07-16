# app/routes/excel_parser.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from io import BytesIO
import pandas as pd

from app.services.extract_data_from_excel import extract_fields_from_excel

router = APIRouter(prefix="/excel", tags=["Excel"])

@router.post("/extract_fields")
async def extract_excel_fields(file: UploadFile = File(...)):
  parsed_data = await extract_fields_from_excel(file)
  return {"extracted_fields": parsed_data}
