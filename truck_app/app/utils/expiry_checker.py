from datetime import date
from sqlalchemy.orm import Session
from app.models.fleet import Fleet
from app.models.kyc import OwnerKYC
from app.utils.notifier import notify_document_expiry

ALERT_DAYS = {30, 7}

DOCUMENT_FIELDS = [
    ("RC Book",    "rc_expiry_date"),
    ("Insurance",  "insurance_expiry_date"),
    ("Permit",     "permit_expiry_date"),
    ("PUC",        "puc_expiry_date"),
]


def check_fleet_expiry(db: Session):
    today = date.today()
    vehicles = db.query(Fleet).filter(Fleet.is_active == True).all()

    for vehicle in vehicles:
        owner = db.query(OwnerKYC).filter(OwnerKYC.id == vehicle.owner_kyc_id).first()
        any_expired = False

        for doc_name, field in DOCUMENT_FIELDS:
            expiry: date = getattr(vehicle, field)
            if expiry is None:
                continue

            days_left = (expiry - today).days

            if days_left < 0:
                any_expired = True
                notify_document_expiry(
                    owner=owner,
                    vehicle=vehicle,
                    doc_name=doc_name,
                    days_left=days_left,
                )
            elif days_left in ALERT_DAYS:
                notify_document_expiry(
                    owner=owner,
                    vehicle=vehicle,
                    doc_name=doc_name,
                    days_left=days_left,
                )

        if any_expired:
            vehicle.is_active = False

    db.commit()
    print(f"[expiry-check] Done — checked {len(vehicles)} vehicle(s) on {today}")
