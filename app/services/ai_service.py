# app/services/ai_service.py

import json
from pymongo import MongoClient
from datetime import datetime
from typing import Optional, List
from fastapi import UploadFile
# AI + Sanity Audit Service
import openai  # Make sure to install openai package if not already
from app.services.llm_model import query_llm
from config import OPENAI_API_KEY
    

# Added later
from app.utils.mongo_helper import get_all_rules, get_case_data_by_id

from .llm_engine import simulate_llm_logic
import os
import openai  # Make sure openai package is installed
from app.utils.prompt_templates import get_llm_prompt
from .rule_engine import apply_rules_to_case
from .file_parser import parse_uploaded_files
from app.utils.mongo_helper import store_case_metadata


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

# This method is not used anywhere in the codebase, but we can use it in the future
# This method only used in the process_user_case method and that method is not used anywhere in the code
def store_case_record(data: dict):
    data["upload_time"] = datetime.utcnow()
    result = cases_col.insert_one(data)
    return str(result.inserted_id)



# This method is not used anywhere in the codebase, but we can use it in the future
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


# This method is not used anywhere in the codebase, but we can use it in the future
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
# This method is not used anywhere in the codebase, but we can use it in the future
# For now we are not using this method anywhere in the codebase
async def analyze_case(case_id: str) -> dict:
    # Step 1: Fetch parsed case data from MongoDB
    case_data = get_case_data_by_id(case_id)
    if not case_data:
        return {"status": "error", "message": "Case not found"}

    response = {"case_id": case_id, "status": "success", "results": {}}

    # Step 2: Run sanity checks
    sanity_issues = perform_basic_sanity_checks(case_data.get("parsed_data", {}))
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
    

# def process_case_for_analysis(case_id: str, parsed_data: dict) -> dict:
#     """
#     This function chains together the steps:
#     1. Run rule engine
#     2. Pass result + parsed data to LLM
#     3. Return a combined report
#     """
#     # Step 1: Apply rules
#     violations = apply_rules_to_case(parsed_data)

#     # Step 2: LLM Analysis
#     ai_result = call_llm_for_analysis(parsed_data, violations)

#     # Step 3: Combine results
#     return {
#         "case_id": case_id,
#         "rule_violations": violations,
#         "ai_result": ai_result
#     }




# ai_service.py


# async def process_case_for_analysis(case_id, user_id, documents=None, metadata=None, context=""):
#     """
#     Main pipeline to parse files, apply rules, call LLM, and store results.
#     """
#     # 1. Parse file uploads (if any)
#     parsed_data = await parse_uploaded_files(documents) if documents else {}

#     # 2. Merge with manual metadata if provided
#     full_case_data = {**parsed_data, **(metadata or {})}

#     # 3. Apply sanity rules or hardcoded checks
#     rule_based_flags = apply_rules_to_case(full_case_data)

#     # 4. Call LLM with the merged metadata and context
#     llm_output = call_llm_for_analysis(full_case_data, context=context)

#     # 5. Store everything in MongoDB
#     store_case_metadata(
#         case_id=case_id,
#         user_id=user_id,
#         metadata=full_case_data,
#         llm_output=llm_output,
#         rule_flags=rule_based_flags,
#         context=context
#     )

#     return {
#         "status": "completed",
#         "rules_detected": rule_based_flags,
#         "llm_analysis": llm_output
#     }



# services/ai_service.py
# from services.file_parser import parse_uploaded_files

async def process_case_for_analysis(case_input: dict):
    metadata = case_input.get("metadata", {})
    files = case_input.get("documents", [])

    extracted_fields = await parse_uploaded_files(files)
    metadata["parsed_documents"] = extracted_fields

    rule_result = apply_rules_to_case(metadata)
    # llm_result = call_llm_for_analysis(metadata)
    rules = get_all_rules()
    # print("Rules fetched:", rules)

    llm_result = simulate_llm_logic(metadata, rules)

    case_record = {}
    case_record["llm_review"] = {
        "llm_flagged": llm_result.get("is_suspicious"),
        "llm_reason": llm_result.get("explanation"),
        "admin_verified": None,
        "admin_feedback": None
    }

    store_case_metadata(case_input["case_id"], case_input["user_id"], metadata, rule_result, llm_result)

    return {
        "status": "completed",
        "rules_checked": rule_result,
        "ai_analysis": llm_result
    }





# ai_service.py

# from .llm_engine import call_llm_for_analysis
# This method is not used anywhere in the codebase, but we can use it in the future
async def audit_training_case_with_llm(case_data: dict) -> dict:
    """
    Uses LLM to validate admin-uploaded case (even if marked 'good').
    Adds flags if anomalies are found.
    """

    llm_result = await call_llm_for_analysis(case_data)

    audit_summary = {
        "llm_flagged": False,
        "issues": [],
        "notes": ""
    }

    if llm_result.get("issues_found"):
        audit_summary["llm_flagged"] = True
        audit_summary["issues"] = llm_result["issues_found"]
        audit_summary["notes"] = "LLM flagged potential inconsistencies in admin-marked case."

    return audit_summary


# This method is not used anywhere in the codebase, but we can use it in the future
async def process_admin_training_case(case_data):
    # Step 1: LLM audit
    audit_report = call_llm_for_analysis(case_data)

    # Step 2: Don't store yet — return findings
    return {
        "status": "audit_complete",
        "llm_flagged": audit_report["flagged"],
        "llm_reasoning": audit_report["reasoning"],
        "case_data": case_data,
        "awaiting_admin_feedback": True
    }


def call_llm_for_analysis_admin(parsed_data: dict, admin_verdict: str) -> dict:
    # Step 1: Apply rules
    rule_results = apply_rules_to_case(parsed_data)

    # Step 2: Ask LLM for its opinion
    llm_verdict, llm_reason = query_llm(parsed_data, rule_results)

    # Step 3: Compare with admin's original label
    is_conflict = (llm_verdict != admin_verdict.lower())

    # Step 4: Return structured audit result
    return {
        "llm_verdict": llm_verdict,
        "llm_reason": llm_reason,
        "admin_verdict": admin_verdict,
        "conflict_flag": is_conflict,
        "rule_results": rule_results
    }