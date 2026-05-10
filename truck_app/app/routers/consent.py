from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import io
from app.database import get_db
from app.schemas.consent import ConsentSubmit, ConsentResponse
from app.models.consent import ConsentLog
from app.models.kyc import CustomerKYC
from app.utils.pdf_generator import generate_consent_pdf, DECLARATION_VERSION

router = APIRouter(prefix="/api/consent", tags=["Consent"])


@router.post("/submit", response_model=ConsentResponse)
def submit_consent(data: ConsentSubmit, request: Request, db: Session = Depends(get_db)):
    if not data.accepted:
        raise HTTPException(status_code=400, detail="Consent must be accepted to proceed")

    customer = db.query(CustomerKYC).filter(CustomerKYC.id == data.customer_kyc_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer KYC record not found")

    already_consented = db.query(ConsentLog).filter(
        ConsentLog.customer_kyc_id == data.customer_kyc_id,
        ConsentLog.accepted == True
    ).first()
    if already_consented:
        raise HTTPException(status_code=400, detail="Customer has already submitted consent")

    ip_address  = request.client.host
    device_info = request.headers.get("user-agent", "Unknown")
    timestamp   = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    log = ConsentLog(
        customer_kyc_id=data.customer_kyc_id,
        accepted=True,
        declaration_version=DECLARATION_VERSION,
        ip_address=ip_address,
        device_info=device_info,
        pdf_url=None,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    # Set pdf_url to our own download endpoint — no Cloudinary access issues
    log.pdf_url = f"/api/consent/pdf/{log.id}"
    db.commit()
    db.refresh(log)
    return log


@router.get("/pdf/{consent_id}")
def download_consent_pdf(consent_id: int, db: Session = Depends(get_db)):
    log = db.query(ConsentLog).filter(ConsentLog.id == consent_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Consent record not found")

    customer = db.query(CustomerKYC).filter(CustomerKYC.id == log.customer_kyc_id).first()

    pdf_bytes = generate_consent_pdf(
        customer_name=f"{customer.first_name} {customer.last_name}",
        mobile=customer.mobile,
        email=customer.email,
        ip_address=log.ip_address,
        device_info=log.device_info or "Unknown",
        timestamp=log.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if log.timestamp else "Unknown",
    )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=consent_{consent_id}.pdf"}
    )


@router.get("/status/{customer_kyc_id}", response_model=ConsentResponse)
def get_consent_status(customer_kyc_id: int, db: Session = Depends(get_db)):
    log = db.query(ConsentLog).filter(
        ConsentLog.customer_kyc_id == customer_kyc_id,
        ConsentLog.accepted == True
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="No consent record found for this customer")
    return log
