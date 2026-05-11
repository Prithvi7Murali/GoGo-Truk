from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class VehicleType(Base):
    __tablename__ = "VEHICLE_TYPE"

    id                  = Column(Integer, primary_key=True, index=True)
    type_name           = Column(String(100), unique=True, nullable=False)
    description         = Column(String(500), nullable=True)
    max_load_capacity   = Column(Float, nullable=True)   # tonnes
    dimensions          = Column(String(200), nullable=True)
    is_active           = Column(Boolean, default=True, nullable=False)
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    updated_at          = Column(DateTime(timezone=True), onupdate=func.now())
