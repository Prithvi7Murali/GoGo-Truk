from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.kyc import KYCCreate, OTPRequest, OTPVerify, KYCResponse
from app.models.kyc import CustomerKYC, OTPStore
from app.utils.cloudinary_client import upload_id_proof
from app.config import settings
import random, string

router = APIRouter(prefix="/api/kyc", tags=["KYC"])

from app.utils.otp_sender import generate_otp, send_otp as dispatch_otp

@router.post("/send-otp")
def send_otp(request: OTPRequest, db: Session = Depends(get_db)):
    """Step 1 — Generate OTP and send via DEV or PROD mode"""
    otp = generate_otp()

    # Delete any old OTPs for this mobile
    db.query(OTPStore).filter(OTPStore.mobile == request.mobile).delete()

    # Save new OTP to database
    otp_record = OTPStore(mobile=request.mobile, otp=otp)
    db.add(otp_record)
    db.commit()

    # Send OTP via DEV or PROD mode
    result = dispatch_otp(
        mobile=request.mobile,
        email=getattr(request, "email", ""),
        otp=otp
    )
    return result

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