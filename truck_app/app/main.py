from fastapi import FastAPI
from app.database import Base, engine
from app.routers import kyc

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="GoGoTruk API",
    description="Logistics platform connecting truck owners with customers",
    version="1.0.0"
)

app.include_router(kyc.router)

@app.get("/")
def root():
    return {"message": "GoGoTruk API is running!"}