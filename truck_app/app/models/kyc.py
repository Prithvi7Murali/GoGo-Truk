from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, Boolean
from sqlalchemy.sql import func
from app.database import Base
import enum

class KYCStatus(str, enum.Enum):
    PENDING  = "Pending"
    VERIFIED = "Verified"
    REJECTED = "Rejected"

class CustomerKYC(Base):
    __tablename__ = "CUSTOMER_KYC"

    id            = Column(Integer, primary_key=True, index=True)
    first_name    = Column(String(100), nullable=False)
    middle_name   = Column(String(100), nullable=True)
    last_name     = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    mobile        = Column(String(15), unique=True, nullable=False)
    email         = Column(String(255), unique=True, nullable=False)
    address_1     = Column(String(255), nullable=False)
    address_2     = Column(String(255), nullable=True)
    address_3     = Column(String(255), nullable=True)
    customer_type = Column(String(50), nullable=False)
    id_proof_url  = Column(String(500), nullable=True)
    otp_verified  = Column(String(5), default="false")
    status        = Column(Enum(KYCStatus), default=KYCStatus.PENDING)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())


class OTPStore(Base):
    __tablename__ = "OTP_STORE"

    id          = Column(Integer, primary_key=True, index=True)
    mobile      = Column(String(15), nullable=False)
    otp         = Column(String(6), nullable=False)
    is_verified = Column(String(5), default="false")
    created_at  = Column(DateTime(timezone=True), server_default=func.now())