from typing import List
from app.models.rule_model import get_all_rules_for_org
from app.utils.logger import logger

# def apply_rules_to_case(parsed_data: dict) -> list:
#     """
#     Applies stored fraud/error/rejection rules on parsed case data.
#     Returns a list of matched rule violations.
#     """
#     violations = []
#     rules = get_all_rules_for_org()  # Can be enhanced to pass org/user context

#     for rule in rules:
#         field = rule.get("field")
#         condition = rule.get("condition")
#         value = rule.get("value")
#         description = rule.get("description")

#         field_value = parsed_data.get(field)

#         if condition == "equals" and field_value == value:
#             violations.append({"field": field, "issue": description})
#         elif condition == "not_equals" and field_value != value:
#             violations.append({"field": field, "issue": description})
#         elif condition == "contains" and value in str(field_value):
#             violations.append({"field": field, "issue": description})
#         elif condition == "greater_than":
#             try:
#                 if float(field_value) > float(value):
#                     violations.append({"field": field, "issue": description})
#             except:
#                 continue
#         elif condition == "less_than":
#             try:
#                 if float(field_value) < float(value):
#                     violations.append({"field": field, "issue": description})
#             except:
#                 continue
#         # Add more conditions here as needed (regex, starts_with, etc.)

#     return violations



def apply_rules_to_case(parsed_cases: List[dict]) -> List[dict]:
    violations = []
    logger.info("Applying rules to parsed data")

    rules = get_all_rules_for_org()

    for case in parsed_cases:
        case_violations = []
        for rule in rules:
            field = rule.get("field")
            condition = rule.get("condition")
            value = rule.get("value")
            description = rule.get("description")

            field_value = case.get(field)

            if condition == "equals" and field_value == value:
                case_violations.append({"field": field, "issue": description})
            elif condition == "not_equals" and field_value != value:
                case_violations.append({"field": field, "issue": description})
            elif condition == "contains" and value in str(field_value):
                case_violations.append({"field": field, "issue": description})
            elif condition == "greater_than":
                try:
                    if float(field_value) > float(value):
                        case_violations.append({"field": field, "issue": description})
                except:
                    continue
            elif condition == "less_than":
                try:
                    if float(field_value) < float(value):
                        case_violations.append({"field": field, "issue": description})
                except:
                    continue

        violations.append({
            "filename": case.get("filename", "unknown"),
            "violations": case_violations
        })

    return violations



