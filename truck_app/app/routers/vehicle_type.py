from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.vehicle_type import VehicleType
from app.schemas.vehicle_type import VehicleTypeCreate, VehicleTypeUpdate, VehicleTypeResponse

admin_router = APIRouter(prefix="/api/admin/vehicle-types", tags=["Admin - Vehicle Types"])
public_router = APIRouter(prefix="/api/vehicle-types", tags=["Vehicle Types"])


# ── Public (used by fleet registration dropdown) ──────────────────────────────

@public_router.get("", response_model=List[VehicleTypeResponse])
def list_vehicle_types(db: Session = Depends(get_db)):
    return db.query(VehicleType).filter(VehicleType.is_active == True).all()


# ── Admin CRUD ────────────────────────────────────────────────────────────────

@admin_router.get("", response_model=List[VehicleTypeResponse])
def admin_list_vehicle_types(db: Session = Depends(get_db)):
    return db.query(VehicleType).order_by(VehicleType.id).all()


@admin_router.post("", response_model=VehicleTypeResponse, status_code=201)
def create_vehicle_type(data: VehicleTypeCreate, db: Session = Depends(get_db)):
    existing = db.query(VehicleType).filter(VehicleType.type_name == data.type_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Vehicle type with this name already exists")
    vt = VehicleType(**data.model_dump())
    db.add(vt)
    db.commit()
    db.refresh(vt)
    return vt


@admin_router.get("/{vehicle_type_id}", response_model=VehicleTypeResponse)
def get_vehicle_type(vehicle_type_id: int, db: Session = Depends(get_db)):
    vt = db.query(VehicleType).filter(VehicleType.id == vehicle_type_id).first()
    if not vt:
        raise HTTPException(status_code=404, detail="Vehicle type not found")
    return vt


@admin_router.put("/{vehicle_type_id}", response_model=VehicleTypeResponse)
def update_vehicle_type(vehicle_type_id: int, data: VehicleTypeUpdate, db: Session = Depends(get_db)):
    vt = db.query(VehicleType).filter(VehicleType.id == vehicle_type_id).first()
    if not vt:
        raise HTTPException(status_code=404, detail="Vehicle type not found")

    if data.type_name is not None:
        duplicate = db.query(VehicleType).filter(
            VehicleType.type_name == data.type_name,
            VehicleType.id != vehicle_type_id,
        ).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="Another vehicle type with this name already exists")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(vt, field, value)

    db.commit()
    db.refresh(vt)
    return vt


@admin_router.delete("/{vehicle_type_id}", status_code=200)
def deactivate_vehicle_type(vehicle_type_id: int, db: Session = Depends(get_db)):
    vt = db.query(VehicleType).filter(VehicleType.id == vehicle_type_id).first()
    if not vt:
        raise HTTPException(status_code=404, detail="Vehicle type not found")
    vt.is_active = False
    db.commit()
    return {"message": f"Vehicle type '{vt.type_name}' deactivated"}
