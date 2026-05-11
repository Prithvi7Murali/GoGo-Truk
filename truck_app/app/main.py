import asyncio
import subprocess
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import kyc
from app.routers import company_kyc
from app.routers import owner_kyc
from app.routers import consent
from app.routers import admin
from app.routers import docs_proxy
from app.routers import fleet
from app.routers.vehicle_type import admin_router as vehicle_type_admin_router
from app.routers.vehicle_type import public_router as vehicle_type_public_router
from app.utils.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        lambda: subprocess.run([sys.executable, "_migrate.py"])
    )
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="GoGoTruk API",
    description="Logistics platform connecting truck owners with customers",
    version="1.0.0",
    lifespan=lifespan,
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
app.include_router(fleet.router)
app.include_router(vehicle_type_admin_router)
app.include_router(vehicle_type_public_router)

@app.get("/")
def root():
    return {"message": "GoGoTruk API is running!"}