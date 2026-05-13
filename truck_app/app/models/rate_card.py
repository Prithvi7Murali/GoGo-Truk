from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class RateCard(Base):
    __tablename__ = "RATE_CARD"

    id              = Column(Integer, primary_key=True, index=True)
    vehicle_type    = Column(String(100), nullable=False)
    distance_from_km = Column(Float, nullable=False)
    distance_to_km  = Column(Float, nullable=True)   # null = no upper limit
    base_fare       = Column(Float, nullable=False)   # minimum charge for this slab
    rate_per_km     = Column(Float, nullable=False)   # per km rate within slab
    is_active       = Column(Boolean, default=True, nullable=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
