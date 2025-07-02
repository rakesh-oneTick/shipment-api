# app/routes/rule_routes.py

from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from app.services.ai_service import process_rule_definition

router = APIRouter(prefix="/rules", tags=["Rules"])

@router.post("/define/")
async def define_rule(
    rule_name: str = Form(...),
    rule_type: str = Form(...),  # fraud, error, rejection
    source: Optional[str] = Form(None),  # Manual, Book, Policy, etc.
    reference_file: Optional[UploadFile] = File(None),
    text_input: Optional[str] = Form(None)
):
    return await process_rule_definition(rule_name, rule_type, source, reference_file, text_input)