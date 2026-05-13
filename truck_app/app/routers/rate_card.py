from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.rate_card import RateCardCreate, RateCardUpdate, RateCardResponse
from app.models.rate_card import RateCard
from app.models.vehicle_type import VehicleType

admin_router  = APIRouter(prefix="/api/admin/rate-cards",  tags=["Admin — Rate Cards"])
public_router = APIRouter(prefix="/api/rate-cards",        tags=["Rate Cards"])


@public_router.get("", response_model=List[RateCardResponse])
def list_rate_cards(db: Session = Depends(get_db)):
    return db.query(RateCard).filter(RateCard.is_active == True).order_by(RateCard.vehicle_type, RateCard.distance_from_km).all()


@admin_router.get("", response_model=List[RateCardResponse])
def list_all_rate_cards(db: Session = Depends(get_db)):
    return db.query(RateCard).order_by(RateCard.vehicle_type, RateCard.distance_from_km).all()


@admin_router.post("", response_model=RateCardResponse, status_code=201)
def create_rate_card(data: RateCardCreate, db: Session = Depends(get_db)):
    vt = db.query(VehicleType).filter(VehicleType.type_name == data.vehicle_type, VehicleType.is_active == True).first()
    if not vt:
        raise HTTPException(status_code=400, detail=f"Invalid or inactive vehicle type: {data.vehicle_type}")

    card = RateCard(**data.model_dump())
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@admin_router.put("/{card_id}", response_model=RateCardResponse)
def update_rate_card(card_id: int, data: RateCardUpdate, db: Session = Depends(get_db)):
    card = db.query(RateCard).filter(RateCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Rate card not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(card, field, value)
    db.commit()
    db.refresh(card)
    return card
