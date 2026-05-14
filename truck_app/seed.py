"""
GoGoTruk seed script — run once on any fresh database.

Seeds:
  1. Vehicle types       (5 standard types)
  2. Rate cards          (per vehicle type, 3 distance slabs each)
  3. Superadmin account  (prompted interactively, or via env vars)

Usage:
    python seed.py

    # Non-interactive (CI / production deploy):
    SEED_ADMIN_USERNAME=admin SEED_ADMIN_EMAIL=admin@gogotruk.com SEED_ADMIN_PASSWORD=changeme python seed.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.vehicle_type import VehicleType
from app.models.rate_card import RateCard
from app.models.admin_user import AdminUser
from app.utils.auth import hash_password

db = SessionLocal()


# ── 1. Vehicle Types ──────────────────────────────────────────────────────────

VEHICLE_TYPES = [
    "Mini Truck",
    "Medium Truck",
    "Large Truck",
    "Container 20ft",
    "Container 40ft",
]

def seed_vehicle_types():
    existing = {v.type_name for v in db.query(VehicleType).all()}
    added = 0
    for name in VEHICLE_TYPES:
        if name not in existing:
            db.add(VehicleType(type_name=name, is_active=True))
            added += 1
    db.commit()
    print(f"[vehicle_types]  {added} added, {len(existing)} already existed")


# ── 2. Rate Cards ─────────────────────────────────────────────────────────────
#
# 3 distance slabs per vehicle type:
#   0–50 km, 51–200 km, 201+ km (no upper limit)
#
# Adjust fares to match your business rates before running in production.

RATE_CARDS = [
    # vehicle_type        from    to      base_fare  rate_per_km
    ("Mini Truck",          0,    50,       800,       12),
    ("Mini Truck",         51,   200,      1500,       10),
    ("Mini Truck",        201,  None,      3000,        8),

    ("Medium Truck",        0,    50,      1200,       16),
    ("Medium Truck",       51,   200,      2500,       14),
    ("Medium Truck",      201,  None,      5000,       12),

    ("Large Truck",         0,    50,      2000,       22),
    ("Large Truck",        51,   200,      4000,       20),
    ("Large Truck",       201,  None,      8000,       18),

    ("Container 20ft",      0,    50,      3000,       28),
    ("Container 20ft",     51,   200,      6000,       25),
    ("Container 20ft",    201,  None,     12000,       22),

    ("Container 40ft",      0,    50,      4500,       35),
    ("Container 40ft",     51,   200,      9000,       32),
    ("Container 40ft",    201,  None,     18000,       28),
]

def seed_rate_cards():
    existing_count = db.query(RateCard).count()
    if existing_count > 0:
        print(f"[rate_cards]     skipped — {existing_count} records already exist")
        return
    for vehicle_type, from_km, to_km, base_fare, rate_per_km in RATE_CARDS:
        db.add(RateCard(
            vehicle_type=vehicle_type,
            distance_from_km=float(from_km),
            distance_to_km=float(to_km) if to_km is not None else None,
            base_fare=float(base_fare),
            rate_per_km=float(rate_per_km),
            is_active=True,
        ))
    db.commit()
    print(f"[rate_cards]     {len(RATE_CARDS)} records added")


# ── 3. Superadmin ─────────────────────────────────────────────────────────────

def seed_superadmin():
    existing = db.query(AdminUser).filter(AdminUser.role == "superadmin").count()
    if existing > 0:
        print(f"[superadmin]     skipped — superadmin already exists")
        return

    username = os.environ.get("SEED_ADMIN_USERNAME")
    email    = os.environ.get("SEED_ADMIN_EMAIL")
    password = os.environ.get("SEED_ADMIN_PASSWORD")

    if not (username and email and password):
        print("\n[superadmin]  No superadmin found. Create one now:")
        username = input("  Username : ").strip()
        email    = input("  Email    : ").strip()
        password = input("  Password : ").strip()

    if not (username and email and password):
        print("[superadmin]     skipped — no input provided")
        return

    db.add(AdminUser(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role="superadmin",
        is_active=True,
    ))
    db.commit()
    print(f"[superadmin]     created → username: {username}")


# ── run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("GoGoTruk seed script\n")
    try:
        seed_vehicle_types()
        seed_rate_cards()
        seed_superadmin()
        print("\nDone. Database is ready.")
    except Exception as e:
        db.rollback()
        print(f"\nError: {e}")
        sys.exit(1)
    finally:
        db.close()
