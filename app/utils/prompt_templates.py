def get_llm_prompt(parsed_data: dict, violations: list) -> str:
    return f"""
You are reviewing a case submission that contains the following data:
{parsed_data}

Known rule violations (if any):
{violations if violations else "None"}

Please identify any potential fraud, inconsistencies, or anomalies based on the data provided.
Give a human-friendly explanation if possible.
"""