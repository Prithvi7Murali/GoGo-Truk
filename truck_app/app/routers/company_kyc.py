from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.kyc import CompanyKYCCreate, CompanyKYCResponse
from app.models.kyc import CompanyKYC
from app.utils.cloudinary_client import upload_document

router = APIRouter(prefix="/api/company-kyc", tags=["Company KYC"])

ALLOWED_TYPES = ["image/jpeg", "image/png", "application/pdf"]


@router.post("/register", response_model=CompanyKYCResponse)
def register_company_kyc(data: CompanyKYCCreate, db: Session = Depends(get_db)):
    existing = db.query(CompanyKYC).filter(CompanyKYC.gst_number == data.gst_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="GST number already registered")

    company = CompanyKYC(**data.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.post("/upload-docs/{company_kyc_id}", response_model=CompanyKYCResponse)
def upload_company_docs(
    company_kyc_id: int,
    incorporation_cert: UploadFile = File(None),
    gst_certificate: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    company = db.query(CompanyKYC).filter(CompanyKYC.id == company_kyc_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company KYC record not found")

    if not incorporation_cert and not gst_certificate:
        raise HTTPException(status_code=400, detail="At least one document must be provided")

    if incorporation_cert:
        if incorporation_cert.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail="incorporation_cert: only JPG, PNG or PDF allowed")
        company.incorporation_cert_url = upload_document(
            incorporation_cert.file.read(), "gogotruk/company-kyc/incorporation"
        )

    if gst_certificate:
        if gst_certificate.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail="gst_certificate: only JPG, PNG or PDF allowed")
        company.gst_certificate_url = upload_document(
            gst_certificate.file.read(), "gogotruk/company-kyc/gst"
        )

    db.commit()
    db.refresh(company)
    return company


@router.get("/status/{company_kyc_id}", response_model=CompanyKYCResponse)
def get_company_kyc_status(company_kyc_id: int, db: Session = Depends(get_db)):
    company = db.query(CompanyKYC).filter(CompanyKYC.id == company_kyc_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company KYC record not found")
    return company
