import math
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.database import get_db
from app.schemas.search import TruckSearchResult, SearchResponse
from app.models.availability import Availability, AvailabilityStatus
from app.models.fleet import Fleet
from app.models.kyc import OwnerKYC
from app.utils.cache import cache_get, cache_set

router = APIRouter(prefix="/api/search", tags=["Search"])

CACHE_TTL = 300  # 5 minutes


@router.get("/trucks", response_model=SearchResponse)
def search_trucks(
    city:       Optional[str]  = None,
    state:      Optional[str]  = None,
    date_from:  Optional[date] = None,
    date_to:    Optional[date] = None,
    date:       Optional[date] = None,
    page:       int = 1,
    page_size:  int = 10,
    db: Session = Depends(get_db),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 50)

    cache_key = f"search:city={city}:state={state}:date={date}:from={date_from}:to={date_to}:p={page}:ps={page_size}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    q = (
        db.query(Availability, Fleet, OwnerKYC)
        .join(Fleet, Fleet.id == Availability.fleet_id)
        .join(OwnerKYC, OwnerKYC.id == Fleet.owner_kyc_id)
        .filter(
            Availability.status == AvailabilityStatus.AVAILABLE,
            Fleet.is_active == True,
        )
    )

    if city:
        q = q.filter(Availability.city.ilike(f"%{city}%"))
    if state:
        q = q.filter(Availability.state.ilike(f"%{state}%"))
    if date:
        q = q.filter(Availability.date == date)
    else:
        if date_from:
            q = q.filter(Availability.date >= date_from)
        if date_to:
            q = q.filter(Availability.date <= date_to)

    total = q.count()
    rows = q.order_by(Availability.date).offset((page - 1) * page_size).limit(page_size).all()

    results = [
        TruckSearchResult(
            availability_id=av.id,
            fleet_id=fl.id,
            date=av.date,
            city=av.city,
            state=av.state,
            vehicle_type=fl.vehicle_type,
            description=fl.description,
            max_load_capacity=fl.max_load_capacity,
            dimensions=fl.dimensions,
            registration_number=fl.registration_number,
            owner_kyc_id=own.id,
            owner_name=f"{own.first_name} {own.last_name}".strip(),
            owner_mobile=own.mobile,
            owner_company=own.company_name,
        )
        for av, fl, own in rows
    ]

    response = SearchResponse(
        results=results,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )

    cache_set(cache_key, response.model_dump(), ttl_seconds=CACHE_TTL)
    return response
