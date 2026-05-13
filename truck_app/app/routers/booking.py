from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.schemas.booking import BookingCreate, BookingReview, BookingResponse
from app.models.booking import Booking
from app.models.availability import Availability, AvailabilityStatus
from app.models.fleet import Fleet
from app.models.kyc import CustomerKYC, KYCStatus, OwnerKYC
from app.utils.cache import acquire_lock, release_lock, cache_delete_pattern

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])

AUTO_REJECT_HOURS = 2


def _dispatch_notification(booking_id: int, background_tasks: BackgroundTasks):
    from app.celery_app import celery_app
    if celery_app:
        try:
            from app.tasks.booking_tasks import send_booking_notification
            send_booking_notification.delay(booking_id)
            return
        except Exception:
            pass
    from app.tasks.booking_tasks import _send_booking_notification
    background_tasks.add_task(_send_booking_notification, booking_id)


def _dispatch_auto_reject(booking_id: int, background_tasks: BackgroundTasks):
    from app.celery_app import celery_app
    if celery_app:
        try:
            from app.tasks.booking_tasks import auto_reject_booking
            auto_reject_booking.apply_async(args=[booking_id], countdown=AUTO_REJECT_HOURS * 3600)
            return
        except Exception:
            pass
    # APScheduler safety net handles this — no extra task needed


@router.post("", response_model=BookingResponse, status_code=201)
def create_booking(data: BookingCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    customer = db.query(CustomerKYC).filter(CustomerKYC.id == data.customer_kyc_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer KYC record not found")
    if customer.status != KYCStatus.VERIFIED:
        raise HTTPException(status_code=403, detail="Customer KYC must be Verified before booking")

    lock_key = f"lock:availability:{data.availability_id}"
    if not acquire_lock(lock_key, ttl=30):
        raise HTTPException(status_code=409, detail="Slot is being processed by another request, try again")

    try:
        slot = (
            db.query(Availability)
            .filter(Availability.id == data.availability_id)
            .with_for_update()
            .first()
        )
        if not slot:
            raise HTTPException(status_code=404, detail="Availability slot not found")
        if slot.status != AvailabilityStatus.AVAILABLE:
            raise HTTPException(status_code=409, detail=f"Slot is not available — current status: {slot.status}")

        slot.status = AvailabilityStatus.BOOKED
        deadline = datetime.now(timezone.utc) + timedelta(hours=AUTO_REJECT_HOURS)

        booking = Booking(
            customer_kyc_id=data.customer_kyc_id,
            availability_id=data.availability_id,
            fleet_id=slot.fleet_id,
            pickup_address=data.pickup_address,
            destination_address=data.destination_address,
            booking_date=slot.date,
            goods_type=data.goods_type,
            goods_weight_kg=data.goods_weight_kg,
            declaration_accepted=data.declaration_accepted,
            owner_response_deadline=deadline,
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)

        cache_delete_pattern("search:*")
        _dispatch_notification(booking.id, background_tasks)
        _dispatch_auto_reject(booking.id, background_tasks)
        return booking
    finally:
        release_lock(lock_key)


@router.post("/{booking_id}/review", response_model=BookingResponse)
def review_booking(booking_id: int, data: BookingReview, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != "Pending":
        raise HTTPException(status_code=409, detail=f"Booking is no longer pending — current status: {booking.status}")

    booking.status = data.action  # store string value directly, not enum member
    booking.rejection_reason = data.reason if data.action == "Rejected" else None

    if data.action == "Rejected":
        slot = db.query(Availability).filter(Availability.id == booking.availability_id).first()
        if slot:
            slot.status = AvailabilityStatus.AVAILABLE
        cache_delete_pattern("search:*")

    db.commit()
    db.refresh(booking)

    customer = db.query(CustomerKYC).filter(CustomerKYC.id == booking.customer_kyc_id).first()
    from app.utils.notifier import notify_booking_reviewed
    if customer:
        background_tasks.add_task(notify_booking_reviewed, customer, booking)

    return booking


@router.get("/owner/{owner_kyc_id}", response_model=List[BookingResponse])
def list_owner_bookings(owner_kyc_id: int, db: Session = Depends(get_db)):
    owner = db.query(OwnerKYC).filter(OwnerKYC.id == owner_kyc_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner KYC record not found")
    fleet_ids = [f.id for f in db.query(Fleet.id).filter(Fleet.owner_kyc_id == owner_kyc_id).all()]
    if not fleet_ids:
        return []
    return (
        db.query(Booking)
        .filter(Booking.fleet_id.in_(fleet_ids))
        .order_by(Booking.status.asc(), Booking.created_at.desc())
        .all()
    )


@router.get("/customer/{customer_kyc_id}", response_model=List[BookingResponse])
def list_customer_bookings(customer_kyc_id: int, db: Session = Depends(get_db)):
    customer = db.query(CustomerKYC).filter(CustomerKYC.id == customer_kyc_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer KYC record not found")
    return (
        db.query(Booking)
        .filter(Booking.customer_kyc_id == customer_kyc_id)
        .order_by(Booking.created_at.desc())
        .all()
    )


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking
