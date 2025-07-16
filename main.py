# backend/main.py
from fastapi import FastAPI
from app.routes import extract_data_using_excel, user_routes, admin_routes, bulk_routes, rule_routes

app = FastAPI()

# Route registration
app.include_router(user_routes.router)
app.include_router(admin_routes.router)
app.include_router(bulk_routes.router)
app.include_router(rule_routes.router)
app.include_router(extract_data_using_excel.router)

@app.get("/")
def root():
    return {"message": "AI Case Analysis Backend Running 🚀"}