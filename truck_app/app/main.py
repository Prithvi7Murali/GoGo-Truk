from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import kyc
from app.routers import company_kyc
from app.routers import owner_kyc
from app.routers import consent
from app.routers import admin
from app.routers import docs_proxy

app = FastAPI(
    title="GoGoTruk API",
    description="Logistics platform connecting truck owners with customers",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kyc.router)
app.include_router(company_kyc.router)
app.include_router(owner_kyc.router)
app.include_router(consent.router)
app.include_router(admin.router)
app.include_router(docs_proxy.router)

@app.get("/")
def root():
    return {"message": "GoGoTruk API is running!"}