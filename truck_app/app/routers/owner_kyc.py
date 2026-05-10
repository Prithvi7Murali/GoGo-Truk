from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.kyc import OwnerKYCCreate, OwnerKYCResponse
from app.models.kyc import OwnerKYC, OTPStore
from app.utils.cloudinary_client import upload_document, upload_pdf_doc

router = APIRouter(prefix="/api/owner-kyc", tags=["Owner KYC"])

ALLOWED_TYPES = ["image/jpeg", "image/png", "application/pdf"]


@router.post("/register", response_model=OwnerKYCResponse)
def register_owner_kyc(data: OwnerKYCCreate, db: Session = Depends(get_db)):
    otp_record = db.query(OTPStore).filter(
        OTPStore.mobile == data.mobile,
        OTPStore.is_verified == "true"
    ).first()
    if not otp_record:
        raise HTTPException(status_code=400, detail="Mobile OTP not verified")

    existing = db.query(OwnerKYC).filter(
        (OwnerKYC.mobile == data.mobile) |
        (OwnerKYC.email == data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mobile or email already registered")

    owner = OwnerKYC(**data.model_dump(), otp_verified="true")
    db.add(owner)
    db.commit()
    db.refresh(owner)
    return owner


@router.post("/upload-docs/{owner_kyc_id}", response_model=OwnerKYCResponse)
def upload_owner_docs(
    owner_kyc_id: int,
    driving_license: UploadFile = File(None),
    owner_id: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    owner = db.query(OwnerKYC).filter(OwnerKYC.id == owner_kyc_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner KYC record not found")

    if not driving_license and not owner_id:
        raise HTTPException(status_code=400, detail="At least one document must be provided")

    if driving_license:
        if driving_license.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail="driving_license: only JPG, PNG or PDF allowed")
        upload_fn = upload_pdf_doc if driving_license.content_type == "application/pdf" else upload_document
        owner.driving_license_url = upload_fn(
            driving_license.file.read(), "gogotruk/owner-kyc/driving-license"
        )

    if owner_id:
        if owner_id.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail="owner_id: only JPG, PNG or PDF allowed")
        upload_fn = upload_pdf_doc if owner_id.content_type == "application/pdf" else upload_document
        owner.owner_id_url = upload_fn(
            owner_id.file.read(), "gogotruk/owner-kyc/owner-id"
        )

    db.commit()
    db.refresh(owner)
    return owner


@router.get("/status/{owner_kyc_id}", response_model=OwnerKYCResponse)
def get_owner_kyc_status(owner_kyc_id: int, db: Session = Depends(get_db)):
    owner = db.query(OwnerKYC).filter(OwnerKYC.id == owner_kyc_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner KYC record not found")
    return owner
