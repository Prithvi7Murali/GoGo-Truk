from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.schemas.fleet import FleetCreate, FleetResponse, FleetExpiryUpdate
from app.models.fleet import Fleet
from app.models.vehicle_type import VehicleType
from app.models.kyc import OwnerKYC, KYCStatus
from app.utils.cloudinary_client import upload_document, upload_pdf_doc
from app.utils.expiry_checker import check_fleet_expiry

router = APIRouter(prefix="/api/fleet", tags=["Fleet"])

ALLOWED_TYPES = ["image/jpeg", "image/png", "application/pdf"]


@router.post("/register", response_model=FleetResponse)
def register_fleet(data: FleetCreate, db: Session = Depends(get_db)):
    owner = db.query(OwnerKYC).filter(OwnerKYC.id == data.owner_kyc_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner KYC record not found")
    if owner.status != KYCStatus.VERIFIED:
        raise HTTPException(status_code=403, detail="Owner KYC must be Verified before registering a vehicle")

    vt = db.query(VehicleType).filter(
        VehicleType.type_name == data.vehicle_type,
        VehicleType.is_active == True,
    ).first()
    if not vt:
        raise HTTPException(status_code=400, detail=f"Invalid or inactive vehicle type: {data.vehicle_type}")

    existing = db.query(Fleet).filter(Fleet.registration_number == data.registration_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Registration number already registered")

    vehicle = Fleet(**data.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.post("/upload-docs/{fleet_id}", response_model=FleetResponse)
def upload_fleet_docs(
    fleet_id: int,
    rc_book: UploadFile = File(None),
    rc_expiry_date: Optional[date] = Form(None),
    insurance: UploadFile = File(None),
    insurance_expiry_date: Optional[date] = Form(None),
    db: Session = Depends(get_db),
):
    vehicle = db.query(Fleet).filter(Fleet.id == fleet_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Fleet record not found")

    if not rc_book and not insurance:
        raise HTTPException(status_code=400, detail="At least one document must be provided")

    if rc_book:
        if rc_book.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail="rc_book: only JPG, PNG or PDF allowed")
        upload_fn = upload_pdf_doc if rc_book.content_type == "application/pdf" else upload_document
        vehicle.rc_book_url = upload_fn(rc_book.file.read(), "gogotruk/fleet/rc-book")
        if rc_expiry_date:
            vehicle.rc_expiry_date = rc_expiry_date

    if insurance:
        if insurance.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail="insurance: only JPG, PNG or PDF allowed")
        upload_fn = upload_pdf_doc if insurance.content_type == "application/pdf" else upload_document
        vehicle.insurance_url = upload_fn(insurance.file.read(), "gogotruk/fleet/insurance")
        if insurance_expiry_date:
            vehicle.insurance_expiry_date = insurance_expiry_date

    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.put("/{fleet_id}/expiry-dates", response_model=FleetResponse)
def update_expiry_dates(fleet_id: int, data: FleetExpiryUpdate, db: Session = Depends(get_db)):
    vehicle = db.query(Fleet).filter(Fleet.id == fleet_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Fleet record not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.post("/run-expiry-check")
def trigger_expiry_check(db: Session = Depends(get_db)):
    check_fleet_expiry(db)
    return {"message": "Expiry check complete"}


@router.get("/owner/{owner_kyc_id}", response_model=List[FleetResponse])
def list_owner_fleet(owner_kyc_id: int, db: Session = Depends(get_db)):
    owner = db.query(OwnerKYC).filter(OwnerKYC.id == owner_kyc_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner KYC record not found")
    return db.query(Fleet).filter(Fleet.owner_kyc_id == owner_kyc_id, Fleet.is_active == True).all()


@router.get("/{fleet_id}", response_model=FleetResponse)
def get_fleet(fleet_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(Fleet).filter(Fleet.id == fleet_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Fleet record not found")
    return vehicle
