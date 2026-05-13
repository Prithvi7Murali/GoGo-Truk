from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class CancellationLog(Base):
    __tablename__ = "CANCELLATION_LOG"

    id                        = Column(Integer, primary_key=True, index=True)
    booking_id                = Column(Integer, ForeignKey("BOOKING.id"), unique=True, nullable=False)
    cancelled_by              = Column(String(10), nullable=False)   # Customer / Owner
    reason                    = Column(String(500), nullable=False)
    hours_before_pickup       = Column(Float, nullable=False)
    cancellation_charge_pct   = Column(Float, nullable=False)        # 0 / 25 / 50
    cancellation_charge_amount = Column(Float, nullable=False)
    refund_amount             = Column(Float, nullable=False)
    refund_status             = Column(String(10), default="Pending", nullable=False)  # Pending / Processed / NA
    created_at                = Column(DateTime(timezone=True), server_default=func.now())
