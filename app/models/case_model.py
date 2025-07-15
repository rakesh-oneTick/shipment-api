# models/case_model.py
from pydantic import BaseModel

# class CaseInput(BaseModel):
#     case_id: str
#     user_id: str
#     metadata: Optional[dict] = None
#     context: Optional[str] = None
#     documents: Optional[List[UploadFile]] = None

from pydantic import BaseModel
from datetime import datetime

from typing import List, Optional

class CaseInput(BaseModel):
    ...
    admin_feedback: Optional["AdminFeedback"] = None



class CaseReviewStatus(BaseModel):
    llm_flagged: Optional[bool] = False        # Did LLM raise a concern?
    llm_reason: Optional[str] = None           # Why LLM thinks it’s bad
    admin_verified: Optional[bool] = None      # Did admin agree?
    admin_feedback: Optional[str] = None       # Optional feedback from admin



class Case(BaseModel):
    case_id: str
    user_id: str
    metadata: Optional[dict] = None
    documents: Optional[List[str]] = None
    upload_time: datetime
    llm_review: Optional[CaseReviewStatus] = None


class AdminFeedback(BaseModel):
    admin_id: Optional[str]
    agrees_with_llm: Optional[bool]
    comment: Optional[str]
    timestamp: Optional[str]


class CaseUploadData(BaseModel):
    case_id: str
    user_id: str
    context: Optional[str] = None
    metadata: Optional[dict] = None
    documents: Optional[List[str]] = None