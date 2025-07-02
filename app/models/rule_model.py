# In app/models/rule_model.py
def get_all_rules_for_org() -> list:
    from app.utils.mongo_helper import get_all_rules
    return get_all_rules()