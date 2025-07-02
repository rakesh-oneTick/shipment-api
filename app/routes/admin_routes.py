from fastapi import APIRouter, UploadFile, File
from typing import List
from app.services.file_parser import parse_document
from app.utils.mongo_helper import insert_case_data  # We assume this exists to save parsed case

router = APIRouter()

@router.post("/admin/upload-cases")
async def upload_cases(files: List[UploadFile] = File(...)):
    parsed_cases = []

    for file in files:
        structured_data = await parse_document(file)
        
        # Save to MongoDB using helper (assumes each file = one case)
        mongo_id = insert_case_data(structured_data)
        
        parsed_cases.append({
            "filename": file.filename,
            "parsed_data": structured_data,
            "mongo_id": str(mongo_id)
        })

    return {"status": "success", "cases_processed": len(parsed_cases), "details": parsed_cases}