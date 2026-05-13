from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.schemas.availability import AvailabilityCreate, AvailabilityUpdate, AvailabilityResponse, BookRequest
from app.models.availability import Availability, AvailabilityStatus
from app.models.fleet import Fleet
from app.models.kyc import KYCStatus, CustomerKYC
from app.utils.cache import acquire_lock, release_lock, cache_delete_pattern

router = APIRouter(prefix="/api/availability", tags=["Availability"])


@router.post("", response_model=List[AvailabilityResponse], status_code=201)
def set_availability(data: AvailabilityCreate, db: Session = Depends(get_db)):
    vehicle = db.query(Fleet).filter(Fleet.id == data.fleet_id, Fleet.is_active == True).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Fleet record not found or inactive")

    # Check for overlapping dates already in the DB for this truck
    existing_dates = {
        row.date for row in
        db.query(Availability.date)
        .filter(
            Availability.fleet_id == data.fleet_id,
            Availability.date.in_(data.dates),
        )
        .all()
    }
    if existing_dates:
        conflicts = sorted(str(d) for d in existing_dates)
        raise HTTPException(
            status_code=409,
            detail=f"Dates already set for this truck: {', '.join(conflicts)}",
        )

    records = [
        Availability(
            fleet_id=data.fleet_id,
            date=d,
            city=data.city,
            state=data.state,
        )
        for d in data.dates
    ]
    db.add_all(records)
    db.commit()
    for r in records:
        db.refresh(r)
    return records


@router.get("/fleet/{fleet_id}", response_model=List[AvailabilityResponse])
def list_fleet_availability(
    fleet_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    vehicle = db.query(Fleet).filter(Fleet.id == fleet_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Fleet record not found")

    q = db.query(Availability).filter(Availability.fleet_id == fleet_id)
    if status:
        q = q.filter(Availability.status == status)
    return q.order_by(Availability.date).all()


@router.get("/search", response_model=List[AvailabilityResponse])
def search_availability(
    city:  Optional[str] = None,
    state: Optional[str] = None,
    date:  Optional[date] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Availability).filter(Availability.status == AvailabilityStatus.AVAILABLE)
    if city:
        q = q.filter(Availability.city.ilike(f"%{city}%"))
    if state:
        q = q.filter(Availability.state.ilike(f"%{state}%"))
    if date:
        q = q.filter(Availability.date == date)
    return q.order_by(Availability.date).all()


@router.put("/{availability_id}", response_model=AvailabilityResponse)
def update_availability(availability_id: int, data: AvailabilityUpdate, db: Session = Depends(get_db)):
    record = db.query(Availability).filter(Availability.id == availability_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Availability record not found")

    if data.date and data.date != record.date:
        conflict = db.query(Availability).filter(
            Availability.fleet_id == record.fleet_id,
            Availability.date == data.date,
            Availability.id != availability_id,
        ).first()
        if conflict:
            raise HTTPException(status_code=409, detail=f"Date {data.date} is already set for this truck")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{availability_id}", status_code=204)
def delete_availability(availability_id: int, db: Session = Depends(get_db)):
    record = db.query(Availability).filter(Availability.id == availability_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Availability record not found")
    if record.status == AvailabilityStatus.BOOKED:
        raise HTTPException(status_code=409, detail="Cannot delete a Booked availability slot")
    db.delete(record)
    db.commit()


@router.post("/{availability_id}/book", response_model=AvailabilityResponse)
def book_slot(availability_id: int, data: BookRequest, db: Session = Depends(get_db)):
    customer = db.query(CustomerKYC).filter(CustomerKYC.id == data.customer_kyc_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer KYC record not found")
    if customer.status != KYCStatus.VERIFIED:
        raise HTTPException(status_code=403, detail="Customer KYC must be Verified before booking a truck")

    lock_key = f"lock:availability:{availability_id}"
    if not acquire_lock(lock_key, ttl=30):
        raise HTTPException(status_code=409, detail="Slot is being processed by another request, try again")

    try:
        # Row-level DB lock prevents concurrent writes even without Redis
        record = (
            db.query(Availability)
            .filter(Availability.id == availability_id)
            .with_for_update()
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Availability record not found")
        if record.status != AvailabilityStatus.AVAILABLE:
            raise HTTPException(status_code=409, detail=f"Slot is not available — current status: {record.status}")

        record.status = AvailabilityStatus.BOOKED
        db.commit()
        db.refresh(record)
        cache_delete_pattern("search:*")
        return record
    finally:
        release_lock(lock_key)


@router.post("/{availability_id}/release", response_model=AvailabilityResponse)
def release_slot(availability_id: int, db: Session = Depends(get_db)):
    lock_key = f"lock:availability:{availability_id}"
    if not acquire_lock(lock_key, ttl=30):
        raise HTTPException(status_code=409, detail="Slot is being processed by another request, try again")

    try:
        record = (
            db.query(Availability)
            .filter(Availability.id == availability_id)
            .with_for_update()
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Availability record not found")
        if record.status != AvailabilityStatus.BOOKED:
            raise HTTPException(status_code=409, detail=f"Slot is not Booked — current status: {record.status}")

        record.status = AvailabilityStatus.AVAILABLE
        db.commit()
        db.refresh(record)
        cache_delete_pattern("search:*")
        return record
    finally:
        release_lock(lock_key)
