# app/services/ai_service.py

import json
from pymongo import MongoClient
from datetime import datetime
from typing import Optional, List
from fastapi import UploadFile
# AI + Sanity Audit Service
import openai  # Make sure to install openai package if not already
from config import OPENAI_API_KEY


# Added later
from app.utils.mongo_helper import get_case_data_by_id
from app.utils.sanity_check import run_sanity_checks
from app.services.rule_engine import apply_rules_to_case
# from app.services.llm_engine import call_llm_for_analysis


import os
import openai  # Make sure openai package is installed
from app.utils.prompt_templates import get_llm_prompt

openai.api_key = os.getenv("OPENAI_API_KEY")

# MongoDB setup
client = MongoClient("mongodb://localhost:27017")
db = client["case_management"]
cases_col = db["uploaded_cases"]
rules_col = db["reference_rules"]

# ----- Helper Functions -----

async def read_files(files: Optional[List[UploadFile]]) -> List[dict]:
    documents = []
    if files:
        for file in files:
            content = await file.read()
            documents.append({
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(content),
                "note": "Stored externally (not in Mongo)"
            })
    return documents

def store_case_record(data: dict):
    data["upload_time"] = datetime.utcnow()
    result = cases_col.insert_one(data)
    return str(result.inserted_id)

# ----- Core Services -----

async def process_user_case(user_id: str, case_id: str, metadata: str, context: str, documents: List[UploadFile]):
    doc_list = await read_files(documents)
    metadata_dict = json.loads(metadata) if metadata else {}
    case = {
        "user_id": user_id,
        "case_id": case_id,
        "metadata": metadata_dict,
        "context": context,
        "documents": doc_list,
        "type": "user"
    }
    case_id = store_case_record(case)
    return {"status": "success", "case_id": case_id}

async def process_admin_upload(admin_id: str, rule_type: str, comments: str, metadata: str, documents: List[UploadFile]):
    doc_list = await read_files(documents)
    metadata_dict = json.loads(metadata) if metadata else {}
    rule = {
        "admin_id": admin_id,
        "rule_type": rule_type,
        "comments": comments,
        "metadata": metadata_dict,
        "documents": doc_list,
        "type": "admin"
    }
    rule["upload_time"] = datetime.utcnow()
    rules_col.insert_one(rule)
    return {"status": "success", "message": "Reference data uploaded successfully."}

async def process_bulk_upload(uploader_id: str, metadata_file: UploadFile, document_files: List[UploadFile], context: str):
    metadata = await metadata_file.read() if metadata_file else None
    metadata_dict = json.loads(metadata.decode()) if metadata else {}
    doc_list = await read_files(document_files)
    case = {
        "uploader_id": uploader_id,
        "metadata": metadata_dict,
        "context": context,
        "documents": doc_list,
        "type": "bulk"
    }
    case_id = store_case_record(case)
    return {"status": "success", "case_id": case_id}

async def process_rule_definition(rule_name: str, rule_type: str, source: str, reference_file: UploadFile, text_input: str):
    ref_doc = await reference_file.read() if reference_file else None
    rule = {
        "rule_name": rule_name,
        "rule_type": rule_type,
        "source": source,
        "reference_note": "Stored externally",
        "rule_text": text_input,
        "upload_time": datetime.utcnow()
    }
    rules_col.insert_one(rule)
    return {"status": "success", "message": "Rule defined and stored."}



openai.api_key = OPENAI_API_KEY

def perform_basic_sanity_checks(metadata: dict) -> List[str]:
    issues = []

    if "phone" in metadata and not str(metadata["phone"]).isdigit():
        issues.append("Phone number field contains non-numeric characters.")
    if "name" in metadata and any(char.isdigit() for char in metadata["name"]):
        issues.append("Name field contains numbers.")
    if "zip" in metadata and len(str(metadata["zip"])) != 5:
        issues.append("ZIP code is not 5 digits.")
    # Add more such common sense rules...

    return issues

def generate_llm_feedback(metadata: dict, context: str) -> str:
    prompt = f"""
    You are an AI auditor. Review the following case metadata and context.
    - Identify if the case seems suspicious, fraudulent, incomplete, or error-prone.
    - Highlight what makes the form weak or strong.
    - Suggest improvements.

    Metadata: {json.dumps(metadata, indent=2)}
    Context: {context}

    Return a short summary in plain English.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o",  # Or "gpt-3.5-turbo" if needed
        messages=[
            {"role": "system", "content": "You are a smart, ethical AI analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=300
    )

    return response.choices[0].message.content.strip()

def audit_uploaded_case(case_id: str):
    case = cases_col.find_one({"_id": case_id})
    if not case:
        return {"status": "error", "message": "Case not found."}

    metadata = case.get("metadata", {})
    context = case.get("context", "")

    sanity_issues = perform_basic_sanity_checks(metadata)
    llm_feedback = generate_llm_feedback(metadata, context)

    return {
        "status": "success",
        "sanity_issues": sanity_issues,
        "llm_feedback": llm_feedback
    }



# Added later
# Main analysis function that combines all steps
async def analyze_case(case_id: str) -> dict:
    # Step 1: Fetch parsed case data from MongoDB
    case_data = get_case_data_by_id(case_id)
    if not case_data:
        return {"status": "error", "message": "Case not found"}

    response = {"case_id": case_id, "status": "success", "results": {}}

    # Step 2: Run sanity checks
    sanity_issues = run_sanity_checks(case_data.get("parsed_data", {}))
    response["results"]["sanity_checks"] = sanity_issues

    # Step 3: Apply user-defined rules
    rule_findings = apply_rules_to_case(case_data.get("parsed_data", {}))
    response["results"]["rule_matches"] = rule_findings

    # Step 4: Get AI/LLM feedback or suggestions
    ai_insights = await call_llm_for_analysis(case_data.get("parsed_data", {}))
    response["results"]["ai_feedback"] = ai_insights

    return response




def call_llm_for_analysis(parsed_data: dict, violations: list = []) -> dict:
    """
    Sends case data and rule violations to LLM for deeper analysis & intelligent reasoning.
    Returns a structured LLM response with explanation.
    """
    prompt = get_llm_prompt(parsed_data, violations)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # You can swap for "gpt-4o", "gpt-3.5-turbo", or "mistral" if custom
            messages=[
                {"role": "system", "content": "You are an intelligent fraud/error analysis assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )

        result = response["choices"][0]["message"]["content"]
        return {
            "status": "success",
            "llm_output": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }