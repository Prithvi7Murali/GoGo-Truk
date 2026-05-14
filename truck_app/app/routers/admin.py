from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.admin import KYCReviewAction, PendingKYCItem
from app.models.kyc import CustomerKYC, CompanyKYC, OwnerKYC, KYCStatus
from app.utils.notifier import notify_kyc_status_change
from app.utils.auth import get_current_admin
from typing import List

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ── Pending queue ─────────────────────────────────────────────────────────────

@router.get("/kyc/pending", response_model=List[PendingKYCItem])
def get_pending_kyc(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    results = []

    for customer in db.query(CustomerKYC).filter(CustomerKYC.status == KYCStatus.PENDING).all():
        results.append(PendingKYCItem(
            id=customer.id,
            kyc_type="Customer",
            name=f"{customer.first_name} {customer.last_name}",
            mobile=customer.mobile,
            email=customer.email,
            status=customer.status.value,
            created_at=customer.created_at,
        ))

    for company in db.query(CompanyKYC).filter(CompanyKYC.status == KYCStatus.PENDING).all():
        results.append(PendingKYCItem(
            id=company.id,
            kyc_type="Company",
            name=company.company_name,
            mobile=company.contact_person_mobile,
            email=company.contact_person_email,
            status=company.status.value,
            created_at=company.created_at,
        ))

    for owner in db.query(OwnerKYC).filter(OwnerKYC.status == KYCStatus.PENDING).all():
        results.append(PendingKYCItem(
            id=owner.id,
            kyc_type="Owner",
            name=f"{owner.first_name} {owner.last_name}",
            mobile=owner.mobile,
            email=owner.email,
            status=owner.status.value,
            created_at=owner.created_at,
        ))

    results.sort(key=lambda x: x.created_at or "", reverse=False)
    return results


# ── Detail views ──────────────────────────────────────────────────────────────

@router.get("/kyc/customer/{kyc_id}")
def get_customer_kyc_detail(kyc_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    record = db.query(CustomerKYC).filter(CustomerKYC.id == kyc_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Customer KYC not found")
    return record


@router.get("/kyc/company/{kyc_id}")
def get_company_kyc_detail(kyc_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    record = db.query(CompanyKYC).filter(CompanyKYC.id == kyc_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Company KYC not found")
    return record


@router.get("/kyc/owner/{kyc_id}")
def get_owner_kyc_detail(kyc_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    record = db.query(OwnerKYC).filter(OwnerKYC.id == kyc_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Owner KYC not found")
    return record


# ── Review actions ────────────────────────────────────────────────────────────

@router.post("/kyc/customer/{kyc_id}/review")
def review_customer_kyc(kyc_id: int, action: KYCReviewAction, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    action.validate_action()
    record = db.query(CustomerKYC).filter(CustomerKYC.id == kyc_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Customer KYC not found")
    if record.status != KYCStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"KYC is already {record.status.value}")

    record.status = KYCStatus.VERIFIED if action.status == "Verified" else KYCStatus.REJECTED
    db.commit()

    notify_kyc_status_change(
        name=f"{record.first_name} {record.last_name}",
        mobile=record.mobile,
        email=record.email,
        kyc_type="Customer",
        status=action.status,
        reason=action.reason or "",
    )
    return {"message": f"Customer KYC {action.status}", "id": kyc_id}


@router.post("/kyc/company/{kyc_id}/review")
def review_company_kyc(kyc_id: int, action: KYCReviewAction, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    action.validate_action()
    record = db.query(CompanyKYC).filter(CompanyKYC.id == kyc_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Company KYC not found")
    if record.status != KYCStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"KYC is already {record.status.value}")

    record.status = KYCStatus.VERIFIED if action.status == "Verified" else KYCStatus.REJECTED
    db.commit()

    notify_kyc_status_change(
        name=record.company_name,
        mobile=record.contact_person_mobile,
        email=record.contact_person_email,
        kyc_type="Company",
        status=action.status,
        reason=action.reason or "",
    )
    return {"message": f"Company KYC {action.status}", "id": kyc_id}


@router.post("/kyc/owner/{kyc_id}/review")
def review_owner_kyc(kyc_id: int, action: KYCReviewAction, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    action.validate_action()
    record = db.query(OwnerKYC).filter(OwnerKYC.id == kyc_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Owner KYC not found")
    if record.status != KYCStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"KYC is already {record.status.value}")

    record.status = KYCStatus.VERIFIED if action.status == "Verified" else KYCStatus.REJECTED
    db.commit()

    notify_kyc_status_change(
        name=f"{record.first_name} {record.last_name}",
        mobile=record.mobile,
        email=record.email,
        kyc_type="Owner",
        status=action.status,
        reason=action.reason or "",
    )
    return {"message": f"Owner KYC {action.status}", "id": kyc_id}


# ── Booking guard (used by future booking endpoints) ──────────────────────────

def assert_kyc_approved(customer_kyc_id: int, db: Session):
    record = db.query(CustomerKYC).filter(CustomerKYC.id == customer_kyc_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Customer KYC not found")
    if record.status != KYCStatus.VERIFIED:
        raise HTTPException(status_code=403, detail="KYC not yet verified. Bookings are blocked until admin approves your KYC.")
