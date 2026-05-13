import enum
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class BookingStatus(str, enum.Enum):
    PENDING   = "Pending"
    CONFIRMED = "Confirmed"
    REJECTED  = "Rejected"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"


class Booking(Base):
    __tablename__ = "BOOKING"

    id                   = Column(Integer, primary_key=True, index=True)
    customer_kyc_id      = Column(Integer, ForeignKey("CUSTOMER_KYC.id"), nullable=False)
    availability_id      = Column(Integer, ForeignKey("AVAILABILITY.id"), nullable=False)
    fleet_id             = Column(Integer, ForeignKey("FLEET.id"), nullable=False)
    pickup_address       = Column(String(500), nullable=False)
    destination_address  = Column(String(500), nullable=False)
    booking_date         = Column(Date, nullable=False)
    goods_type           = Column(String(200), nullable=False)
    goods_weight_kg      = Column(Float, nullable=False)
    declaration_accepted = Column(Boolean, nullable=False)
    status                  = Column(String(20), default="Pending", nullable=False)
    rejection_reason        = Column(String(500), nullable=True)
    owner_response_deadline = Column(DateTime(timezone=True), nullable=True)
    created_at              = Column(DateTime(timezone=True), server_default=func.now())
    updated_at              = Column(DateTime(timezone=True), onupdate=func.now())
