from fastapi import APIRouter
from app.utils.mongo_helper import store_case_metadata


router = APIRouter()

@router.post("/submit_admin_feedback")
async def submit_admin_feedback(payload: dict):
    """
    Payload must include:
    - case_data: original case structure
    - llm_flagged: bool
    - llm_reasoning: str
    - admin_verdict: bool (True = agree with LLM)
    - admin_reasoning: str (required if disagreeing)
    """

    case_data = payload.get("case_data", {})
    case_data["llm_audit_summary"] = {
        "flagged": payload["llm_flagged"],
        "llm_reasoning": payload["llm_reasoning"],
        "admin_final_verdict": payload["admin_verdict"],
        "admin_reasoning": payload["admin_reasoning"]
    }

    # Store in DB
    await store_case_metadata(case_data)

    return {"status": "stored_with_feedback"}