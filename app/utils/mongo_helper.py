from pymongo import MongoClient
from datetime import datetime
from fastapi import UploadFile
from typing import List, Optional

from pymongo import DESCENDING
from app.models.rule_model import RuleResult

# 🔌 Setup Mongo client (make sure it's consistent with other parts of your app)
client = MongoClient("mongodb://localhost:27017")
db = client["case_management"]
parsed_cases_collection = db["parsed_cases"]
rules_collection = db["reference_rules"]  # Assuming you have a collection for rules
cases_collection = db["uploaded_cases"]
training_collection = db["training_cases"]


#  This is a sample function to fetch all rules from the database.
# It assumes you have a collection named "rules" in your MongoDB database.
# I will update this function later to include more complex logic as needed.
def get_all_rules():
    return list(rules_collection.find({}, {"_id": 0}));


def get_case_data_by_id(case_id: str):
    """
    Fetch a single case from MongoDB by its case_id
    """
    return cases_collection.find_one({"case_id": case_id})



def insert_case_data(data: dict):
    """
    Insert structured OCR-parsed case data into MongoDB.
    Returns the Mongo document ID.
    """
    result = parsed_cases_collection.insert_one(data)
    return result.inserted_id


# Used in upload_case in process_case_for_analysis in ai_service.py
async def store_case_metadata(
    user_id: str,
    context: Optional[str],
    metadata: Optional[dict],
    documents: Optional[List[UploadFile]]
) -> str:
    case_record = {
        "user_id": user_id,
        "context": context,
        "metadata": metadata,
        "upload_time": datetime.utcnow(),
        "documents": []
    }

    if documents:
        for file in documents:
            contents = await file.read()
            case_record["documents"].append({
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(contents),
                "note": "Stored in blob/storage (future implementation)"
            })

    result = cases_collection.insert_one(case_record)
    return str(result.inserted_id)


def get_training_cases(limit=50):
    """
    Fetch past admin-uploaded cases for training.
    Assumes these are marked with a special 'is_training_data': True flag.
    """
    training_cases = cases_collection.find(
        {"is_training_data": True},
        {"_id": 0, "metadata": 1, "llm_feedback": 1, "rule_matches": 1}
    ).limit(limit)

    return list(training_cases)



# mongo_helper.py

def fetch_recent_feedback_entries(limit: int = 20):
    """
    Fetch the most recent feedback entries where the LLM/AI was marked incorrect
    """
    feedback_collection = db["feedback_entries"]  # Make sure this is your feedback collection name
    entries = feedback_collection.find(
        {"llm_accuracy": "wrong"},  # or "incorrect", depending on your schema
        {"_id": 0, "case_id": 1, "comments": 1, "suggested_action": 1, "created_at": 1}
    ).sort("created_at", DESCENDING).limit(limit)

    return list(entries)


# used in upload_case in app/routes/user_routes.py
def attach_llm_result_to_case(case_id: str, result: RuleResult):
    cases_collection.update_one(
        {"case_id": case_id},
        {"$set": {
            "llm_result": {
                "passed": result.passed,
                "reason": result.reason
            }}
        }
    )


def add_admin_feedback(case_id: str, feedback: dict):
    feedback["timestamp"] = datetime.utcnow().isoformat()
    result = cases_collection.update_one(
        {"case_id": case_id},
        {"$set": {"admin_feedback": feedback}}
    )
    return result.modified_count


def store_llm_feedback(feedback_data: dict):
    feedback_data["timestamp"] = datetime.utcnow().isoformat()
    db["llm_feedback"].insert_one(feedback_data)


def get_all_cases() -> list:
    return list(cases_collection.find({}))

def store_case_with_audit(case_id: str,
                        #   uploader: str,
                          parsed_data: dict,
                          rule_results: dict,
                          llm_verdict: str,
                          llm_reason: str):
    
    record = {
        "case_id": case_id,
        # "uploader": uploader,
        "parsed_data": parsed_data,
        "rule_results": rule_results,
        "ai_verdict": {
            "decision": llm_verdict,
            "reason": llm_reason
        },
        "audited_by_ai": True,
        "timestamp": datetime.utcnow()
    }

    result = training_collection.insert_one(record)
    return str(result.inserted_id)