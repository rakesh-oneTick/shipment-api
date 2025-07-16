from datetime import datetime
from fastapi import APIRouter, UploadFile, File
from typing import List, Optional

from pymongo import MongoClient
from app.models.case_model import AdminFeedback,CaseInputWithDocuments
from app.services.ai_service import call_llm_for_analysis_admin
from app.services.file_parser import parse_document
from app.utils.mongo_helper import get_case_data_by_id, insert_case_data, store_pending_training_case  # We assume this exists to save parsed case

from fastapi import HTTPException
from pydantic import BaseModel
from app.services.llm_feedback_engine import record_feedback
from app.utils.mongo_helper import add_admin_feedback
from app.utils.mongo_helper import get_all_cases

from typing import List, Optional
from app.services.file_parser import parse_uploaded_files
from app.utils.mongo_helper import store_case_with_audit
from app.services.ai_service import apply_rules_to_case

client = MongoClient("mongodb://localhost:27017")
db = client["case_management"]
cases_collection = db["llm_feedback"]
pending_training_cases = db["pending_training_cases"]

router = APIRouter()



# ✅ File: admin_routes.py

# from fastapi import APIRouter, UploadFile, Form
# from typing import Optional, List
# from app.services.file_parser import parse_uploaded_files
# from app.utils.mongo_helper import store_case_with_audit
# import json

# router = APIRouter()

# @router.post("/upload_training_case/")
# async def upload_training_case(
#     user_id: str = Form(...),
#     case_type: str = Form(...),  # "good" or "bad"
#     files: Optional[List[UploadFile]] = None,
#     metadata: Optional[str] = Form(None),  # JSON string if coming via frontend form
#     context: Optional[str] = Form(None)
# ):
#     # Step 1: Parse uploaded files (PDFs, images, etc.)
#     parsed_data = await parse_uploaded_files(files)

#     # Step 2: Load metadata (e.g., from Excel)
#     metadata_dict = json.loads(metadata) if metadata else {}

#     # Step 3: Apply rules
#     rule_result = apply_rules_to_case(parsed_data)

#     # Step 4: Call LLM to analyze for suspiciousness
#     llm_result = call_llm_for_analysis_admin(parsed_data,case_type)

#     # Step 5: Store the full case with LLM audit
#     result = store_case_with_audit(
#         user_id=user_id,
#         metadata=metadata_dict,
#         parsed_data=parsed_data,
#         context=context,
#         # rule_result=rule_result,
#         llm_result=llm_result,
#         verdict=case_type
#     )

#     return {"status": "success", "mongo_id": result}


@router.post("/upload_training_case")
async def upload_training_case(case: CaseInputWithDocuments):
    # 1. Parse data (could be Excel, image, etc.)
    parsed_data = parse_uploaded_files(case.documents)
    
    # 2. Apply rules
    rule_result = apply_rules_to_case(parsed_data)

    # 3. Call LLM for deeper reasoning
    llm_result = call_llm_for_analysis_admin(parsed_data, rule_result)

    # 4. If admin said it's "good", but LLM finds issues
    if case.metadata.get("label") == "good" and llm_result.get("verdict") == "bad":
        # Attach everything + explanation + original label
        flagged_case = {
            "case_id": case.case_id,
            "user_id": case.user_id,
            "parsed_data": parsed_data,
            "admin_label": "good",
            "llm_verdict": "bad",
            "llm_reason": llm_result.get("reason"),
            "timestamp": datetime.utcnow(),
            "status": "pending_admin_feedback"
        }

        # 5. Store in pending collection
        pending_id = store_pending_training_case(flagged_case)

        return {
            "status": "flagged",
            "message": "LLM flagged this 'good' case as potentially bad.",
            "pending_case_id": pending_id,
            "llm_reason": llm_result.get("reason")
        }

    # 6. Otherwise — store as normal training case
    full_record = {
        "case_id": case.case_id,
        "user_id": case.user_id,
        "parsed_data": parsed_data,
        # "rules": rule_result,
        "llm_analysis": llm_result,
        "label": case.metadata.get("label"),
        "timestamp": datetime.utcnow()
    }

    mongo_id = store_case_with_audit(full_record)

    return {"status": "success", "mongo_id": mongo_id}


# We are not using this route anymore, but keeping it for reference
@router.post("/admin/upload-cases")
async def upload_cases(files: List[UploadFile] = File(...)):
    parsed_cases = []

    for file in files:
        structured_data = await parse_document(file)
         
        # Save to MongoDB using helper (assumes each file = one case)
        mongo_id = await insert_case_data(structured_data)
        
        parsed_cases.append({
            "filename": file.filename,       
            "parsed_data": structured_data,
            "mongo_id": str(mongo_id)
        })


    # case_record ={
    #     "case_id":case_input.case_id,
    # }

    return {"status": "success", "cases_processed": len(parsed_cases), "details": parsed_cases}


class FeedbackInput(BaseModel):
    case_id: str
    ai_label: str  # "good" or "bad"
    admin_label: str  # "good" or "bad"
    rationale: str = ""  # Optional explanation


# This route is duplicate
@router.post("/admin/submit_feedback")
def submit_feedback(feedback: FeedbackInput):
    if feedback.admin_label not in ["good", "bad"] or feedback.ai_label not in ["good", "bad"]:
        raise HTTPException(status_code=400, detail="Invalid label. Use 'good' or 'bad'.")

    result = record_feedback(
        case_id=feedback.case_id,
        original_ai_label=feedback.ai_label,
        admin_label=feedback.admin_label,
        rationale=feedback.rationale
    )
    return result



@router.post("/admin/review_case/{case_id}")
def review_case(case_id: str, is_llm_correct: bool, feedback: Optional[str] = None):
    case = get_case_data_by_id(case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    review_data = {
        "llm_review.admin_verified": is_llm_correct,
        "llm_review.admin_feedback": feedback
    }
    cases_collection.update_one({"case_id": case_id}, {"$set": review_data})

    return {"status": "review updated", "case_id": case_id}


@router.post("/admin/feedback_on_case/{case_id}")
def feedback_on_case(case_id: str, feedback: AdminFeedback):
    # No need to manually convert to dict here because it's done in the helper
    result = add_admin_feedback(case_id, feedback)
    
    if result == 1:
        return {"status": "feedback_saved", "case_id": case_id}
    else:
        return {"status": "no_change", "message": "Case not found or feedback not updated"}



# This route is duplicate
# @router.post("/admin/submit_feedback")
# def submit_feedback(feedback: LLMFeedback):
#     store_llm_feedback(feedback.dict())
#     return {"status": "success", "message": "Feedback recorded"}


@router.get("/admin/case_dashboard")
def get_admin_case_dashboard():
    cases = get_all_cases()
    case_list = []

    for case in cases:
        case_list.append({
            "case_id": case.get("case_id"),
            "user_id": case.get("user_id"),
            "uploaded_on": case.get("upload_time"),
            "status": case.get("ai_result", {}).get("final_decision", "pending"),
            "rule_flags": case.get("rule_flags", []),
            "feedback_count": len(case.get("feedback", [])),
        })

    return {
        "status": "success",
        "total_cases": len(case_list),
        "cases": case_list
    }


@router.get("/pending_training_cases")
def get_pending_training_cases():
    return list(pending_training_cases.find({}, {"_id": 0}))


#  
class AdminTrainingFeedback(BaseModel):
    case_id: str
    verdict: str  # either "agree_with_llm" or "override"
    reason: Optional[str] = None  # required if override



@router.post("/submit_training_feedback")
def submit_training_feedback(feedback: AdminTrainingFeedback):
    case = pending_training_cases.find_one({"case_id": feedback.case_id})
    if not case:
        return {"status": "error", "message": "Case not found in pending queue."}

    # Add admin verdict to record
    case["admin_verdict"] = feedback.verdict
    case["admin_reason"] = feedback.reason
    case["finalized_timestamp"] = datetime.utcnow()

    # Insert into final training cases DB
    # store_case_metadata(case)
    store_case_with_audit(case)

    # Remove from pending queue
    pending_training_cases.delete_one({"case_id": feedback.case_id})

    return {"status": "success", "message": "Feedback recorded and case finalized."}