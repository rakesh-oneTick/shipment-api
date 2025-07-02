# app/routes/bulk_routes.py

from fastapi import APIRouter, UploadFile, File, Form
from typing import List, Optional
from app.services.ai_service import process_bulk_upload

router = APIRouter(prefix="/bulk", tags=["Bulk"])

@router.post("/upload/")
async def upload_bulk_data(
    uploader_id: str = Form(...),
    metadata_file: Optional[UploadFile] = File(None),
    document_files: Optional[List[UploadFile]] = File(None),
    context: Optional[str] = Form(None)
):
    return await process_bulk_upload(uploader_id, metadata_file, document_files, context)