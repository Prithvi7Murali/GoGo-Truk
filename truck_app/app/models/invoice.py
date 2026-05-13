from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Invoice(Base):
    __tablename__ = "INVOICE"

    id                  = Column(Integer, primary_key=True, index=True)
    invoice_number      = Column(String(30), unique=True, nullable=False)
    booking_id          = Column(Integer, ForeignKey("BOOKING.id"), unique=True, nullable=False)
    customer_kyc_id     = Column(Integer, ForeignKey("CUSTOMER_KYC.id"), nullable=False)
    distance_km         = Column(Float, nullable=False)
    base_fare           = Column(Float, nullable=False)
    waiting_charges     = Column(Float, default=0.0, nullable=False)
    toll_charges        = Column(Float, default=0.0, nullable=False)
    loading_charges     = Column(Float, default=0.0, nullable=False)
    total_before_gst    = Column(Float, nullable=False)
    gst_type            = Column(String(10), nullable=False)   # CGST+SGST or IGST
    cgst_rate           = Column(Float, nullable=False)
    sgst_rate           = Column(Float, nullable=False)
    igst_rate           = Column(Float, nullable=False)
    cgst_amount         = Column(Float, nullable=False)
    sgst_amount         = Column(Float, nullable=False)
    igst_amount         = Column(Float, nullable=False)
    total_amount        = Column(Float, nullable=False)
    invoice_pdf_url     = Column(String(500), nullable=True)
    status              = Column(String(10), default="Draft", nullable=False)  # Draft / Sent
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    updated_at          = Column(DateTime(timezone=True), onupdate=func.now())
