from app.models.rule_model import get_all_rules_for_org

def apply_rules_to_case(parsed_data: dict) -> list:
    """
    Applies stored fraud/error/rejection rules on parsed case data.
    Returns a list of matched rule violations.
    """
    violations = []
    rules = get_all_rules_for_org()  # Can be enhanced to pass org/user context

    for rule in rules:
        field = rule.get("field")
        condition = rule.get("condition")
        value = rule.get("value")
        description = rule.get("description")

        field_value = parsed_data.get(field)

        if condition == "equals" and field_value == value:
            violations.append({"field": field, "issue": description})
        elif condition == "not_equals" and field_value != value:
            violations.append({"field": field, "issue": description})
        elif condition == "contains" and value in str(field_value):
            violations.append({"field": field, "issue": description})
        elif condition == "greater_than":
            try:
                if float(field_value) > float(value):
                    violations.append({"field": field, "issue": description})
            except:
                continue
        elif condition == "less_than":
            try:
                if float(field_value) < float(value):
                    violations.append({"field": field, "issue": description})
            except:
                continue
        # Add more conditions here as needed (regex, starts_with, etc.)

    return violations