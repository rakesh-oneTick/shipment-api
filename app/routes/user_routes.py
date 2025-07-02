# app/routes/user_routes.py

from fastapi import APIRouter, UploadFile, File, Form
from typing import List, Optional
from app.services.ai_service import process_user_case

router = APIRouter(prefix="/user", tags=["User"])

@router.post("/upload-case/")
async def upload_case(
    user_id: str = Form(...),
    case_id: str = Form(...),
    metadata: Optional[str] = Form(None),
    context: Optional[str] = Form(None),
    documents: Optional[List[UploadFile]] = File(None)
):
    return await process_user_case(user_id, case_id, metadata, context, documents)