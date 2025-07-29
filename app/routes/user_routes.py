# # app/routes/user_routes.py

# from fastapi import APIRouter, UploadFile, File, Form
# from typing import List, Optional
# from app.services.ai_service import process_user_case

# router = APIRouter(prefix="/user", tags=["User"])

# @router.post("/upload-case/")
# async def upload_case(
#     user_id: str = Form(...),
#     case_id: str = Form(...),
#     metadata: Optional[str] = Form(None),
#     context: Optional[str] = Form(None),
#     documents: Optional[List[UploadFile]] = File(None)
# ):
#     return await process_user_case(user_id, case_id, metadata, context, documents)



# from fastapi import APIRouter, UploadFile, Form
# from fastapi import File
# from typing import List, Optional
# from pydantic import BaseModel
# from ..services.ai_service import process_case_for_analysis

# router = APIRouter()

# class CaseUploadInput(BaseModel):
#     case_id: str
#     user_id: str
#     metadata: Optional[dict] = None
#     context: Optional[str] = None

# @router.post("/upload_case/")
# async def upload_case(
#     case_id: str = Form(...),
#     user_id: str = Form(...),
#     context: Optional[str] = Form(""),
#     metadata: Optional[str] = Form(None),  # Expecting JSON string
#     documents: Optional[List[UploadFile]] = File(None)
# ):
#     import json
#     metadata_dict = json.loads(metadata) if metadata else {}

#     result = await process_case_for_analysis(
#         case_id=case_id,
#         user_id=user_id,
#         documents=documents,
#         metadata=metadata_dict,
#         context=context
#     )

#     return {
#         "message": "Case uploaded and processed successfully.",
#         "analysis_result": result
#     }

  

# routes/user_routes.py
# from asyncio.log import logger
from fastapi import APIRouter, UploadFile, Form
from typing import List, Optional
from fastapi.params import File
from pydantic import BaseModel
from app.models.rule_model import get_all_rules_for_org
from app.services.ai_service import process_case_for_analysis
from app.services.file_parser import parse_uploaded_files
from app.utils.mongo_helper import get_case_data_by_id, get_training_cases, store_case_metadata

# from app.models.case_model import  CaseUploadData
# from app.services.ai_service import process_case_for_analysis
from app.services.ai_service import call_llm_for_analysis
from app.utils.mongo_helper import attach_llm_result_to_case
import json

router = APIRouter()

class CaseUploadRequest(BaseModel):
    user_id: str
    case_id: Optional[str] = None
    metadata: Optional[dict] = None
    context: Optional[str] = None
    documents: Optional[List[UploadFile]] = None


@router.post("/upload_case/")
async def upload_case(    case_id: str = Form(...),
    user_id: str = Form(...),
    context: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),  # JSON string
    documents: List[UploadFile] = File(...)
       ):
    print("Upload user case method")
    
    case_input = {
        "case_id": case_id,
        "user_id": user_id,
        "context": context,
        "metadata": json.loads(metadata) if metadata else {},
        "documents": documents  # Read file content
    }

    # case_input = CaseUploadData(
    #     case_id=case_id,
    #     user_id=user_id,
    #     context=context,
    #     metadata=json.loads(metadata) if metadata else {},
    #     documents=documents
    # )


    # Step 1: Process and store case
    # case_id = await process_case_for_analysis(case_input)
    # extracted_fields = await process_case_for_analysis(case_input.get("documents", []))
    # print(f"Extracted fields: {extracted_fields}")

    extracted_fields = await parse_uploaded_files(case_input.get("documents", []))

    uploaded_case_id= await store_case_metadata(
        user_id=case_input["user_id"],
        context=case_input.get("context"),
        metadata=metadata,
        extracted_fields  = extracted_fields,
    )

    # print(f"Extracted fields: {extracted_fields}")
    # Step 2: Run LLM analysis

    rules = get_all_rules_for_org()    
    all_cases = get_training_cases();

    # print(f"All cases: {all_cases}")
    # return {
    #     "data":"fetched successfully"
    # }
    # return "data processed"
    llm_result = call_llm_for_analysis(extracted_fields,rules,all_cases)

    # Step 3: Attach LLM result to the case
    attach_llm_result_to_case(uploaded_case_id, llm_result)
    reason = llm_result.get("reason")

    # If the reason is missing (None) or is the literal string "None.", replace it.
    if not reason or reason.strip().lower() in ["none", "none."]:
        final_reason = "Cases passed without issues"
    else:
        final_reason = reason
    # --- End of new logic ---
        
    return {
        "status": "uploaded and analyzed",
        # "case_id": uploaded_case_id,
        "llm_decision": llm_result.get("decision", "No decision made"),
        "reason": final_reason, # Use the processed reason
    }



@router.get("/user/case_result/{case_id}")
def get_user_case_result(case_id: str):
    
    result = get_case_data_by_id(case_id)
    if result:
        return {
            "status": "success",
            "case_id": case_id,
            "analysis_result": result.get("ai_result", {}),
            "rule_flags": result.get("rule_flags", []),
            "feedback": result.get("feedback", []),
            "submitted_by": result.get("user_id"),
            "submitted_on": result.get("upload_time"),
        }
    else:
        return {"status": "error", "message": "Case not found"}

