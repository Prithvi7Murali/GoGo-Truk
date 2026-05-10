from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class ConsentLog(Base):
    __tablename__ = "CONSENT_LOG"

    id                  = Column(Integer, primary_key=True, index=True)
    customer_kyc_id     = Column(Integer, ForeignKey("CUSTOMER_KYC.id"), nullable=False)
    accepted            = Column(Boolean, nullable=False)
    declaration_version = Column(String(10), nullable=False)
    ip_address          = Column(String(45), nullable=False)
    device_info         = Column(String(500), nullable=True)
    pdf_url             = Column(String(500), nullable=True)
    timestamp           = Column(DateTime(timezone=True), server_default=func.now())
