import json
import datetime
import math

# Use a try-except block in case the 'bson' library is not installed
# in a different environment.
try:
    from bson import ObjectId
except ImportError:
    ObjectId = None

def json_converter(o):
    """
    A robust JSON converter to handle special data types from databases.
    """
    # Handles datetime objects
    if isinstance(o, (datetime.datetime, datetime.date)):
        return o.isoformat()
    # Handles MongoDB's ObjectId
    if ObjectId and isinstance(o, ObjectId):
        return str(o)
    # Handles 'not a number' float values (like pandas' NaN)
    if isinstance(o, float) and math.isnan(o):
        return "N/A" # Convert NaN to a more readable string for the LLM
    # Raise an error for any other unhandled types
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

def get_llm_prompt(parsed_data: dict, rules: list, training_cases: list) -> str:
    """
    Builds a detailed and robust prompt including business rules and few-shot examples.
    This function safely handles missing keys and various data types.
    """
    
    # 1. Start with the core instruction and rules
    prompt_sections = [
        "You are an expert document fraud and error detection analyst for a logistics company.",
        "Your task is to analyze the provided shipping document data based on a set of rules and historical examples.",
        "You must decide if the data should be 'Accept' or 'Reject' and provide a clear reason for your decision.",
        "\n## Business Rules to Enforce:",
    ]
    
    # Safely append rule descriptions
    if rules:
        for rule in rules:
            # Use .get() to avoid crashing if 'description' key is missing
            description = rule.get('description', 'No description provided for this rule.')
            prompt_sections.append(f"- {description}")
        
    # 2. Add the historical cases as few-shot examples
    prompt_sections.append("\n## Historical Analysis Examples:")
    
    if training_cases:
        for case in training_cases:
            # Safely extract all data points using .get() for robustness
            example_data = case.get('parsed_data', {})
            decision_label = case.get('metadata', {}).get('label', 'Unknown').capitalize()
            reason = case.get('ai_verdict', {}).get('reason', 'No reason was provided.')
            
            # Use the robust converter to handle all special types (ObjectId, datetime, nan)
            example_data_str = json.dumps(example_data, indent=2, default=json_converter)
            
            example_str = (
                f"### Example Case:\n"
                f"Input Data:\n```json\n{example_data_str}\n```\n"
                f"Correct Decision: {decision_label}\n"
                f"Reason: {reason}"
            )
            prompt_sections.append(example_str)
        
    # 3. Add the new case to be analyzed
    new_case_data_str = json.dumps(parsed_data, indent=2, default=json_converter)
    prompt_sections.append("\n" + "="*40 + "\n")
    prompt_sections.append("## New Case for Your Analysis:")
    prompt_sections.append(
        "Based on the rules and examples above, analyze the following new case."
    )
    prompt_sections.append(
        f"Input Data:\n```json\n{new_case_data_str}\n```"
    )
    
    # 4. Specify the exact output format you want
    prompt_sections.append("\n## Your Task:")
    prompt_sections.append(
        "Provide your analysis in the following format ONLY:\n"
        "Decision: [Accept/Reject]\n"
        "Issue: [Provide a concise, single-sentence reason for your decision. If accepted, state 'None'.]"
    )
    
    return "\n".join(prompt_sections)

# def get_llm_prompt(parsed_data: dict, rules: list) -> str:
#     return f"""
# You are a strict shipping compliance officer.

# Based on the following rules:
# {rules}

# Review this data:
# {parsed_data}

# If any rule is violated, summarize the issue briefly (within 30 words) and respond with:
# Decision: Reject

# If no issue is found:
# Decision: Accept 
# """
