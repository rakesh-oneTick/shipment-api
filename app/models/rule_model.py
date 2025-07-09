from pydantic import BaseModel
from typing import Optional

def get_all_rules_for_org() -> list:
    from app.utils.mongo_helper import get_all_rules
    return get_all_rules()


class LLMFeedback(BaseModel):
    case_id: str
    ai_decision: str  # e.g., "good" or "bad"
    admin_decision: str  # "agree", "disagree"
    reason: Optional[str] = None  # Optional explanation from admin
    timestamp: Optional[str] = None


class RuleResult(BaseModel):
    passed: bool
    reason: str