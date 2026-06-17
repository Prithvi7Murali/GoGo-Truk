from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.kyc import OwnerKYCCreate, OwnerKYCResponse, OTPRequest, OTPVerify
from app.models.kyc import OwnerKYC, OTPStore
from app.utils.cloudinary_client import upload_document, upload_pdf_doc
from app.utils.otp_sender import generate_otp, send_otp as dispatch_otp

router = APIRouter(prefix="/api/owner-kyc", tags=["Owner KYC"])

ALLOWED_TYPES = ["image/jpeg", "image/png", "application/pdf"]


@router.post("/send-otp")
def send_owner_otp(request: OTPRequest, db: Session = Depends(get_db)):
    """Step 1 — Send OTP to truck owner mobile"""
    otp = generate_otp()

    db.query(OTPStore).filter(OTPStore.mobile == request.mobile).delete()

    otp_record = OTPStore(mobile=request.mobile, otp=otp)
    db.add(otp_record)
    db.commit()

    result = dispatch_otp(
        mobile=request.mobile,
        email=getattr(request, "email", ""),
        otp=otp
    )
    return result


@router.post("/verify-otp")
def verify_owner_otp(request: OTPVerify, db: Session = Depends(get_db)):
    """Step 2 — Verify OTP entered by truck owner"""
    otp_record = db.query(OTPStore).filter(
        OTPStore.mobile == request.mobile,
        OTPStore.otp == request.otp
    ).first()

    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    otp_record.is_verified = "true"
    db.commit()
    return {"message": "OTP verified successfully"}


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