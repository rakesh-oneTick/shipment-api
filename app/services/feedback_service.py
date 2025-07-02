from typing import Optional
from openai import BaseModel
from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017")
db = client["case_management"]
feedback_col = db["case_feedback"]

class FeedbackInput(BaseModel):
    case_id: str
    user_id: str
    was_ai_correct: bool
    feedback_text: Optional[str] = None
    timestamp: Optional[datetime] = None

def store_user_feedback(feedback: FeedbackInput):
    record = {
        "case_id": feedback.case_id,
        "user_id": feedback.user_id,
        "was_ai_correct": feedback.was_ai_correct,
        "feedback_text": feedback.feedback_text or "",
        "timestamp": feedback.timestamp or datetime.utcnow()
    }

    result = feedback_col.insert_one(record)
    return {"status": "saved", "id": str(result.inserted_id)}