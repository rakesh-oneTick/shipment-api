from datetime import datetime
import os
from openai import OpenAI
from app.utils.logger import logger
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def query_llm(parsed_data: dict, rules: list) -> tuple[str, str]:
    # logger.info("Inside query_llm function")

    current_date = datetime.utcnow().date().isoformat()

    prompt = (
        "You are an expert compliance analyst reviewing a new case submission.\n\n"
        f"Today's date: {current_date}\n\n"
        "Case Data:\n"
        f"{parsed_data}\n\n"
        "Rules to Check:\n"
        f"{rules}\n\n"
        "Please follow these instructions carefully:\n"
        "1. Review each rule thoroughly.\n"
        "2. Check if each rule is violated based on the case data.\n"
        "3. Only if a rule is clearly violated, consider the case as 'bad'.\n"
        "4. If no rule is violated, mark the case as 'good'.\n\n"
        "Now provide your decision in this exact format:\n"
        "Verdict: good or bad\n"
        "Reason: <brief reason in 1 short sentence, max 20 words>"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a compliance analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )

        content = response.choices[0].message.content.strip()

        verdict, reason = "unknown", "No reason provided"
        for line in content.splitlines():
            if "verdict:" in line.lower():
                verdict = line.split(":", 1)[1].strip().lower()
            elif "reason:" in line.lower():
                reason = line.split(":", 1)[1].strip()

        # Trim reason to max 20 words
        reason = ' '.join(reason.split()[:20])

        return verdict, reason

    except Exception as e:
        logger.error(f"LLM call failed: {str(e)}")
        return "unknown", "LLM call failed due to an error."








# from openai import OpenAI  # Unused right now but fine to keep
# import os
# from app.utils.logger import logger

# def query_llm(parsed_data: dict, rules: list) -> tuple[str, str]:
#     logger.info("Inside query_llm function")
#     prompt = (
#     "You are an expert compliance analyst. A case has been submitted with the following data:\n"
#     f"{parsed_data}\n\n"
#     "The following rule violations or observations were detected:\n"
#     f"{rules}\n\n"
#     "Based on the data and rules, do you recommend accepting or rejecting this case?\n\n"
#     "Return only one word: 'accept' or 'reject', and give a brief reason why."
# )

#     # (Fake LLM call here for MVP, you can plug real API later)
#     # Simulate with deterministic rule fallback
#     if rules:  # Correct way to check if list has violations
#         return "reject", "Violations found in rule check."
#     else:
#         return "accept", "No issues found. Case looks valid."



