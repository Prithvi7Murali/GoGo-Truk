
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, ForeignKey
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


class CompanyType(str, enum.Enum):
    PVT_LTD     = "Pvt Ltd"
    LLP         = "LLP"
    PARTNERSHIP = "Partnership"
    LIMITED     = "Limited"


class CompanyKYC(Base):
    __tablename__ = "COMPANY_KYC"

    id                     = Column(Integer, primary_key=True, index=True)
    company_name           = Column(String(255), nullable=False)
    company_type           = Column(Enum(CompanyType), nullable=False)
    gst_number             = Column(String(15), unique=True, nullable=False)
    registered_address_1   = Column(String(255), nullable=False)
    registered_address_2   = Column(String(255), nullable=True)
    registered_address_3   = Column(String(255), nullable=True)
    city                   = Column(String(100), nullable=False)
    state                  = Column(String(100), nullable=False)
    pincode                = Column(String(6), nullable=False)
    contact_person_name    = Column(String(200), nullable=False)
    contact_person_mobile  = Column(String(15), nullable=False)
    contact_person_email   = Column(String(255), nullable=False)
    incorporation_cert_url = Column(String(500), nullable=True)
    gst_certificate_url    = Column(String(500), nullable=True)
    status                 = Column(Enum(KYCStatus), default=KYCStatus.PENDING)
    customer_kyc_id        = Column(Integer, ForeignKey("CUSTOMER_KYC.id"), nullable=False)
    created_at             = Column(DateTime(timezone=True), server_default=func.now())
    updated_at             = Column(DateTime(timezone=True), onupdate=func.now())


class OwnerKYC(Base):
    __tablename__ = "OWNER_KYC"

    id                   = Column(Integer, primary_key=True, index=True)
    first_name           = Column(String(100), nullable=False)
    middle_name          = Column(String(100), nullable=True)
    last_name            = Column(String(100), nullable=False)
    date_of_birth        = Column(Date, nullable=False)
    mobile               = Column(String(15), unique=True, nullable=False)
    email                = Column(String(255), unique=True, nullable=False)
    company_name         = Column(String(255), nullable=True)
    address_1            = Column(String(255), nullable=False)
    address_2            = Column(String(255), nullable=True)
    address_3            = Column(String(255), nullable=True)
    driving_license_url  = Column(String(500), nullable=True)
    owner_id_url         = Column(String(500), nullable=True)
    otp_verified         = Column(String(5), default="false")
    status               = Column(Enum(KYCStatus), default=KYCStatus.PENDING)
    created_at           = Column(DateTime(timezone=True), server_default=func.now())
    updated_at           = Column(DateTime(timezone=True), onupdate=func.now())


class OTPStore(Base):
    __tablename__ = "OTP_STORE"

    id          = Column(Integer, primary_key=True, index=True)
    mobile      = Column(String(15), nullable=False)
    otp         = Column(String(6), nullable=False)
    is_verified = Column(String(5), default="false")
    created_at  = Column(DateTime(timezone=True), server_default=func.now())