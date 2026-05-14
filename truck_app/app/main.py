import asyncio
import os
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
from app.routers import availability
from app.routers import search
from app.routers import booking
from app.routers.rate_card import admin_router as rate_card_admin_router
from app.routers.rate_card import public_router as rate_card_public_router
from app.routers import invoice
from app.routers import cancellation
from app.routers import admin_auth
from app.routers import admin_dashboard
from app.routers import analytics
from app.utils.scheduler import start_scheduler, stop_scheduler


def _auto_seed():
    from app.database import SessionLocal
    from app.models.vehicle_type import VehicleType
    from app.models.rate_card import RateCard
    from app.models.admin_user import AdminUser
    from app.utils.auth import hash_password

    VEHICLE_TYPES = [
        "Mini Truck", "Medium Truck", "Large Truck", "Container 20ft", "Container 40ft",
    ]
    RATE_CARDS = [
        ("Mini Truck",       0,    50,   800,  12),
        ("Mini Truck",      51,   200,  1500,  10),
        ("Mini Truck",     201,  None,  3000,   8),
        ("Medium Truck",     0,    50,  1200,  16),
        ("Medium Truck",    51,   200,  2500,  14),
        ("Medium Truck",   201,  None,  5000,  12),
        ("Large Truck",      0,    50,  2000,  22),
        ("Large Truck",     51,   200,  4000,  20),
        ("Large Truck",    201,  None,  8000,  18),
        ("Container 20ft",   0,    50,  3000,  28),
        ("Container 20ft",  51,   200,  6000,  25),
        ("Container 20ft", 201,  None, 12000,  22),
        ("Container 40ft",   0,    50,  4500,  35),
        ("Container 40ft",  51,   200,  9000,  32),
        ("Container 40ft", 201,  None, 18000,  28),
    ]

    db = SessionLocal()
    try:
        # vehicle types
        existing_types = {v.type_name for v in db.query(VehicleType).all()}
        added = [VehicleType(type_name=n, is_active=True) for n in VEHICLE_TYPES if n not in existing_types]
        if added:
            db.add_all(added)
            db.commit()
            print(f"[seed] {len(added)} vehicle type(s) added")

        # rate cards
        if db.query(RateCard).count() == 0:
            db.add_all([
                RateCard(
                    vehicle_type=vt,
                    distance_from_km=float(f),
                    distance_to_km=float(t) if t else None,
                    base_fare=float(b),
                    rate_per_km=float(r),
                    is_active=True,
                )
                for vt, f, t, b, r in RATE_CARDS
            ])
            db.commit()
            print(f"[seed] {len(RATE_CARDS)} rate card(s) added")

        # superadmin — from .env only; no interactive prompt on server startup
        if db.query(AdminUser).filter(AdminUser.role == "superadmin").count() == 0:
            from app.config import settings
            username = settings.SEED_ADMIN_USERNAME
            email    = settings.SEED_ADMIN_EMAIL
            password = settings.SEED_ADMIN_PASSWORD
            if username and email and password:
                db.add(AdminUser(
                    username=username,
                    email=email,
                    password_hash=hash_password(password),
                    role="superadmin",
                    is_active=True,
                ))
                db.commit()
                print(f"[seed] Superadmin created → username: {username}")
            else:
                print("[seed] WARNING: No superadmin exists.")
                print("[seed]   Set SEED_ADMIN_USERNAME / SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD env vars,")
                print("[seed]   or call POST /api/admin/auth/setup to create one.")
    except Exception as e:
        db.rollback()
        print(f"[seed] Error: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        lambda: subprocess.run([sys.executable, "_migrate.py"])
    )
    _auto_seed()
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
app.include_router(availability.router)
app.include_router(search.router)
app.include_router(booking.router)
app.include_router(rate_card_admin_router)
app.include_router(rate_card_public_router)
app.include_router(invoice.router)
app.include_router(cancellation.router)
app.include_router(admin_auth.router)
app.include_router(admin_dashboard.router)
app.include_router(analytics.router)

@app.get("/")
def root():
    return {"message": "GoGoTruk API is running!"}