# app/services/llm_feedback_engine.py

from datetime import datetime
from pymongo import MongoClient

# Mongo setup
client = MongoClient("mongodb://localhost:27017")
db = client["case_management"]
feedback_collection = db["llm_feedback"]

def record_feedback(case_id: str, original_ai_label: str, admin_label: str, rationale: str = ""):
    """
    Stores admin feedback on AI decision.
    """
    feedback = {
        "case_id": case_id,
        "ai_label": original_ai_label,
        "admin_label": admin_label,
        "rationale": rationale,
        "timestamp": datetime.utcnow()
    }
    feedback_collection.insert_one(feedback)

    # Optionally, this is where future logic can “learn” from confirmed patterns
    print(f"🧠 Feedback stored for case: {case_id}")
    return {"status": "feedback stored", "case_id": case_id}