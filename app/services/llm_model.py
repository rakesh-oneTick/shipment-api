# llm_model.py

# Optional: Replace this later with actual call to Mistral, OpenAI etc.
# from openai import OpenAI  # Example if using OpenAI SDK

# llm_model.py

# from .llm_engine import generate_improved_prompt  # 🔁 importing from Step 1B

# def query_llm(base_prompt: str, case_data: dict) -> dict:
#     """
#     Sends improved prompt and case data to the LLM and gets back the result.
#     """
#     # Inject feedback-learned enhancements
#     final_prompt = generate_improved_prompt(base_prompt)

#     # You can construct the full input here
#     llm_input = f"""{final_prompt}

# # 📄 Case Data:
# {case_data}

# Respond with your analysis (pass/fail) and reason."""

#     # --- MOCKED RESPONSE: replace this with real LLM API later ---
#     response = {
#         "decision": "pass",
#         "reason": "Case meets all compliance and pattern checks (simulated)."
#     }

#     return response



# from openai import OpenAI
# import os

# def query_llm(parsed_data: dict, rule_results: dict) -> tuple[str, str]:
#     prompt = f"""
# You are an expert compliance analyst. A case has been submitted with the following data:
# {parsed_data}

# The following rule violations or observations were detected:
# {rule_results}

# Based on the data and rule results, do you recommend accepting or rejecting this case? 

# Return only one word: 'accept' or 'reject', and give a brief reason why.
#     """
    
#     # (Fake LLM call here for MVP, you can plug real API later)
#     # Simulate with deterministic rule fallback
#     if any(rule_results.values()):
#         return "reject", "Violations found in rule check."
#     else:
#         return "accept", "No issues found. Case looks valid."



from openai import OpenAI  # Unused right now but fine to keep
import os

def query_llm(parsed_data: dict, rule_results: list) -> tuple[str, str]:
    prompt = (
    "You are an expert compliance analyst. A case has been submitted with the following data:\n"
    f"{parsed_data}\n\n"
    "The following rule violations or observations were detected:\n"
    f"{rule_results}\n\n"
    "Based on the data and rule results, do you recommend accepting or rejecting this case?\n\n"
    "Return only one word: 'accept' or 'reject', and give a brief reason why."
)

    # (Fake LLM call here for MVP, you can plug real API later)
    # Simulate with deterministic rule fallback
    if rule_results:  # Correct way to check if list has violations
        return "reject", "Violations found in rule check."
    else:
        return "accept", "No issues found. Case looks valid."
