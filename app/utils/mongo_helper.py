from pymongo import MongoClient

# 🔌 Setup Mongo client (make sure it's consistent with other parts of your app)
client = MongoClient("mongodb://localhost:27017")
db = client["case_management"]
parsed_cases_collection = db["parsed_cases"]

def insert_case_data(data: dict):
    """
    Insert structured OCR-parsed case data into MongoDB.
    Returns the Mongo document ID.
    """
    result = parsed_cases_collection.insert_one(data)
    return result.inserted_id