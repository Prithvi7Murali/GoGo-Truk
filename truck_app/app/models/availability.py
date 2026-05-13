import enum
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class AvailabilityStatus(str, enum.Enum):
    AVAILABLE  = "Available"
    BOOKED     = "Booked"
    CANCELLED  = "Cancelled"


class Availability(Base):
    __tablename__ = "AVAILABILITY"

    id         = Column(Integer, primary_key=True, index=True)
    fleet_id   = Column(Integer, ForeignKey("FLEET.id"), nullable=False)
    date       = Column(Date, nullable=False)
    city       = Column(String(100), nullable=False)
    state      = Column(String(100), nullable=False)
    status     = Column(Enum(AvailabilityStatus), default=AvailabilityStatus.AVAILABLE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("fleet_id", "date", name="uq_fleet_date"),
    )
