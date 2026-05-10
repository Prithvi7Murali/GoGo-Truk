"""
Run once to insert sample KYC records for local development/testing.
Usage: python seed.py
"""
from datetime import date
from app.database import SessionLocal
from app.models.kyc import CustomerKYC, OTPStore, KYCStatus


SAMPLE_CUSTOMERS = [
    {
        "first_name": "Ravi",
        "last_name": "Kumar",
        "date_of_birth": date(1990, 6, 15),
        "mobile": "9876543210",
        "email": "ravi.kumar@example.com",
        "address_1": "12 MG Road",
        "customer_type": "Individual",
        "status": KYCStatus.VERIFIED,
        "otp_verified": "true",
    },
    {
        "first_name": "Priya",
        "last_name": "Sharma",
        "date_of_birth": date(1985, 3, 22),
        "mobile": "9123456780",
        "email": "priya.sharma@example.com",
        "address_1": "45 Brigade Road",
        "customer_type": "Individual",
        "status": KYCStatus.PENDING,
        "otp_verified": "false",
    },
    {
        "first_name": "Amit",
        "last_name": "Logistics",
        "date_of_birth": date(1978, 11, 5),
        "mobile": "9012345678",
        "email": "amit@amitlogistics.com",
        "address_1": "78 Industrial Area",
        "customer_type": "Business",
        "status": KYCStatus.REJECTED,
        "otp_verified": "true",
    },
]


def seed():
    db = SessionLocal()
    try:
        inserted = 0
        for data in SAMPLE_CUSTOMERS:
            exists = db.query(CustomerKYC).filter_by(mobile=data["mobile"]).first()
            if not exists:
                db.add(CustomerKYC(**data))
                inserted += 1
        db.commit()
        print(f"Seeded {inserted} customer(s). ({len(SAMPLE_CUSTOMERS) - inserted} already existed)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
