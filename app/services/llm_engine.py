# # llm_engine.py

# import openai  # Or any future LLM connector
# import os

# # For mocking response now
# def call_llm_for_analysis(case_metadata: dict, context: str = "") -> dict:
#     """
#     Simulates calling an LLM to analyze case metadata and provide insights.

#     :param case_metadata: Parsed case data from files or manual input
#     :param context: Optional additional context provided by user
#     :return: AI-driven analysis (observations, suggestions, red flags etc.)
#     """

#     # 1. Prepare prompt (simple template — can improve later!)
#     prompt = f"""You are an intelligent document auditor. 
#     Review the following case data and suggest any errors, fraud patterns, or red flags.

#     Context: {context}

#     Case Metadata:
#     {case_metadata}

#     Provide:
#     - Observations
#     - Suggested corrections (if any)
#     - Fraud/error likelihood
#     - Confidence score (0–100)
#     """

#     # 2. Mocking LLM response (replace with real OpenAI/Mistral call later)
#     simulated_response = {
#         "observations": ["Date of birth seems inconsistent with ID issued year."],
#         "suggestions": ["Verify if applicant age is valid based on DOB."],
#         "fraud_likelihood": "Moderate",
#         "confidence": 82,
#         "llm_model": "Kaio-Simulated-Audit-v1"
#     }

#     return simulated_response

# 🧠 You can later replace the above mock with real call like:
# openai.ChatCompletion.create(...) with appropriate API key and model


# llm_engine.py


# from app.utils.mongo_helper import get_training_cases
# from app.services.llm_model import query_llm  # We'll define this next

# from app.models.rule_model import RuleResult
# from app.utils.mongo_helper import get_case_data_by_id
# from .llm_model import query_llm

# Define Rule type as a Dict for now (customize as needed)
from typing import List, Dict, Any
from app.utils.mongo_helper import fetch_recent_feedback_entries
Rule = Dict[str, Any]


def simulate_llm_logic(parsed_data: dict, rules: List[Rule]) -> dict:
    """
    Runs LLM logic on the parsed data and rule set.
    Returns result dict: { is_suspicious: bool, explanation: str }
    """

    # Simulated prompt to LLM
    suspicious = False
    explanation = "Looks fine based on rules."

    # Example simple logic
    for rule in rules:
        if rule["field"] in parsed_data:
            if not parsed_data[rule["field"]].startswith(rule["expected_start"]):
                suspicious = True
                explanation = f"{rule['field']} failed rule: {rule['description']}"
                break

    return {
        "is_suspicious": suspicious,
        "explanation": explanation
    }


def generate_improved_prompt(base_prompt: str) -> str:
    """
    Enhances the original LLM prompt by injecting insights from recent feedback.
    """
    feedback_entries = fetch_recent_feedback_entries()

    if not feedback_entries:
        return base_prompt  # No feedback to learn from

    improved_sections = []

    for entry in feedback_entries:
        suggestion = entry.get("suggested_action", "")
        comment = entry.get("comments", "")
        case_id = entry.get("case_id", "")
        if suggestion or comment:
            improved_sections.append(
                f"From past error (case ID: {case_id}): {suggestion or comment}"
            )

    if not improved_sections:
        return base_prompt

    # Construct new prompt
    feedback_note = "\n".join(improved_sections)
    enhanced_prompt = f"""{base_prompt}

# 🔁 Feedback Learning Section:
Please consider these learnings from previous feedback:
{feedback_note}

Then proceed with your analysis."""

    return enhanced_prompt