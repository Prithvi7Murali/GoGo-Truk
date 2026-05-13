from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.schemas.cancellation import CancellationRequest, CancellationPreview, CancellationResponse
from app.models.cancellation import CancellationLog
from app.models.booking import Booking
from app.models.availability import Availability, AvailabilityStatus
from app.models.invoice import Invoice
from app.models.kyc import CustomerKYC, OwnerKYC
from app.models.fleet import Fleet
from app.utils.cache import cache_delete_pattern

router = APIRouter(prefix="/api/bookings", tags=["Cancellation"])

CANCELLABLE_STATUSES = {"Pending", "Confirmed"}


def _hours_before_pickup(booking_date) -> float:
    pickup_dt = datetime(booking_date.year, booking_date.month, booking_date.day, tzinfo=timezone.utc)
    delta = (pickup_dt - datetime.now(timezone.utc)).total_seconds()
    return round(delta / 3600, 2)


def _charge_pct(hours: float) -> float:
    if hours > 48:
        return 0.0
    elif hours > 24:
        return 25.0
    else:
        return 50.0


def _get_invoice_total(db: Session, booking_id: int) -> float:
    invoice = db.query(Invoice).filter(Invoice.booking_id == booking_id).first()
    return invoice.total_amount if invoice else 0.0


def _process_refund(cancellation_id: int):
    from app.database import SessionLocal
    from app.models.cancellation import CancellationLog
    from app.utils.notifier import notify_cancellation

    db = SessionLocal()
    try:
        log      = db.query(CancellationLog).filter(CancellationLog.id == cancellation_id).first()
        booking  = db.query(Booking).filter(Booking.id == log.booking_id).first()
        customer = db.query(CustomerKYC).filter(CustomerKYC.id == booking.customer_kyc_id).first()
        fleet    = db.query(Fleet).filter(Fleet.id == booking.fleet_id).first()
        owner    = db.query(OwnerKYC).filter(OwnerKYC.id == fleet.owner_kyc_id).first()

        # Production: call payment gateway refund API here
        if log.refund_amount > 0:
            log.refund_status = "Processed"
        else:
            log.refund_status = "NA"
        db.commit()

        notify_cancellation(customer, owner, booking, log)
    finally:
        db.close()


@router.get("/{booking_id}/cancellation-preview", response_model=CancellationPreview)
def preview_cancellation(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status not in CANCELLABLE_STATUSES:
        raise HTTPException(status_code=409, detail=f"Booking cannot be cancelled — status: {booking.status}")

    hours        = _hours_before_pickup(booking.booking_date)
    pct          = _charge_pct(hours) if booking.status == "Confirmed" else 0.0
    invoice_total = _get_invoice_total(db, booking_id)
    charge       = round(invoice_total * pct / 100, 2)
    refund       = round(invoice_total - charge, 2)

    return CancellationPreview(
        booking_id=booking_id,
        booking_date=str(booking.booking_date),
        hours_before_pickup=hours,
        cancellation_charge_pct=pct,
        cancellation_charge_amount=charge,
        refund_amount=refund,
        invoice_total=invoice_total if invoice_total > 0 else None,
    )


@router.post("/{booking_id}/cancel", response_model=CancellationResponse, status_code=201)
def cancel_booking(
    booking_id: int,
    data: CancellationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status not in CANCELLABLE_STATUSES:
        raise HTTPException(status_code=409, detail=f"Booking cannot be cancelled — status: {booking.status}")

    existing = db.query(CancellationLog).filter(CancellationLog.booking_id == booking_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Booking already has a cancellation record")

    hours         = _hours_before_pickup(booking.booking_date)
    pct           = _charge_pct(hours) if booking.status == "Confirmed" else 0.0
    invoice_total = _get_invoice_total(db, booking_id)
    charge        = round(invoice_total * pct / 100, 2)
    refund        = round(invoice_total - charge, 2)

    # Release availability slot
    slot = db.query(Availability).filter(Availability.id == booking.availability_id).first()
    if slot:
        slot.status = AvailabilityStatus.AVAILABLE

    booking.status = "Cancelled"

    log = CancellationLog(
        booking_id=booking_id,
        cancelled_by=data.cancelled_by,
        reason=data.reason,
        hours_before_pickup=hours,
        cancellation_charge_pct=pct,
        cancellation_charge_amount=charge,
        refund_amount=refund,
        refund_status="Pending" if refund > 0 else "NA",
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    cache_delete_pattern("search:*")
    background_tasks.add_task(_process_refund, log.id)
    return log


@router.get("/{booking_id}/cancellation", response_model=CancellationResponse)
def get_cancellation(booking_id: int, db: Session = Depends(get_db)):
    log = db.query(CancellationLog).filter(CancellationLog.booking_id == booking_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="No cancellation record for this booking")
    return log
