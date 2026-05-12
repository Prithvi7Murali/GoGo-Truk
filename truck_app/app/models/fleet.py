from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Fleet(Base):
    __tablename__ = "FLEET"

    id                    = Column(Integer, primary_key=True, index=True)
    owner_kyc_id          = Column(Integer, ForeignKey("OWNER_KYC.id"), nullable=False)
    vehicle_type          = Column(String(100), nullable=False)
    description           = Column(String(500), nullable=True)
    max_load_capacity     = Column(Float, nullable=True)
    dimensions            = Column(String(200), nullable=True)
    registration_number   = Column(String(20), unique=True, nullable=False)
    engine_number         = Column(String(50), nullable=False)
    chassis_number        = Column(String(50), nullable=False)
    rc_book_url           = Column(String(500), nullable=True)
    rc_expiry_date        = Column(Date, nullable=True)
    insurance_url         = Column(String(500), nullable=True)
    insurance_expiry_date = Column(Date, nullable=True)
    permit_url            = Column(String(500), nullable=True)
    permit_expiry_date    = Column(Date, nullable=True)
    puc_url               = Column(String(500), nullable=True)
    puc_expiry_date       = Column(Date, nullable=True)
    is_active             = Column(Boolean, default=True, nullable=False)
    created_at            = Column(DateTime(timezone=True), server_default=func.now())
    updated_at            = Column(DateTime(timezone=True), onupdate=func.now())
