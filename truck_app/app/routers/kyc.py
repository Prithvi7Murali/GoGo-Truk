from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.kyc import KYCCreate, OTPRequest, OTPVerify, KYCResponse
from app.models.kyc import CustomerKYC, OTPStore
from app.utils.cloudinary_client import upload_id_proof
from app.config import settings
import random, string

router = APIRouter(prefix="/api/kyc", tags=["KYC"])

@router.post("/send-otp")
def send_otp(request: OTPRequest, db: Session = Depends(get_db)):
    """Step 1 — Generate and store OTP in database"""
    otp = "".join(random.choices(string.digits, k=6))

    # Delete any old OTPs for this mobile
    db.query(OTPStore).filter(OTPStore.mobile == request.mobile).delete()

    otp_record = OTPStore(mobile=request.mobile, otp=otp)

    if settings.DEV_MODE:
        # Auto-verify in dev — no real SMS sent, phone numbers flow straight through
        otp_record.is_verified = "true"

    db.add(otp_record)
    db.commit()

    response = {"message": "OTP sent successfully"}
    if settings.DEV_MODE:
        response["dev_otp"] = otp  # expose OTP in response for dev/testing only
    return response

@router.post("/verify-otp")
def verify_otp(request: OTPVerify, db: Session = Depends(get_db)):
    """Step 2 — Verify OTP from database"""
    otp_record = db.query(OTPStore).filter(
        OTPStore.mobile == request.mobile,
        OTPStore.otp == request.otp
    ).first()

    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # Mark as verified
    otp_record.is_verified = "true"
    db.commit()
    return {"message": "OTP verified successfully"}

@router.post("/register", response_model=KYCResponse)
def register_kyc(data: KYCCreate, db: Session = Depends(get_db)):
    """Step 3 — Submit KYC form after OTP verified"""
    # Check OTP was verified
    otp_record = db.query(OTPStore).filter(
        OTPStore.mobile == data.mobile,
        OTPStore.is_verified == "true"
    ).first()

    if not otp_record:
        raise HTTPException(status_code=400, detail="Mobile OTP not verified")

    # Check duplicate mobile or email
    existing = db.query(CustomerKYC).filter(
        (CustomerKYC.mobile == data.mobile) |
        (CustomerKYC.email == data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mobile or email already registered")

    kyc = CustomerKYC(**data.model_dump(), otp_verified="true")
    db.add(kyc)
    db.commit()
    db.refresh(kyc)
    return kyc

@router.post("/upload-id/{kyc_id}")
def upload_id(kyc_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Step 4 — Upload ID proof document"""
    kyc = db.query(CustomerKYC).filter(CustomerKYC.id == kyc_id).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC record not found")

    allowed_types = ["image/jpeg", "image/png", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPG, PNG or PDF allowed")

    file_data = file.file.read()
    file_path = upload_id_proof(file_data, file.filename, file.content_type)
    kyc.id_proof_url = file_path
    db.commit()
    return {"message": "ID proof uploaded", "file_path": file_path}

@router.get("/status/{kyc_id}", response_model=KYCResponse)
def get_kyc_status(kyc_id: int, db: Session = Depends(get_db)):
    """Check KYC status"""
    kyc = db.query(CustomerKYC).filter(CustomerKYC.id == kyc_id).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC record not found")
    return kyc