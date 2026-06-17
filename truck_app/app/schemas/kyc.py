from pydantic import BaseModel, EmailStr, field_validator
from datetime import date
from typing import Optional
import re

class KYCCreate(BaseModel):
    first_name:    str
    middle_name:   Optional[str] = None
    last_name:     str
    date_of_birth: date
    mobile:        str
    email:         EmailStr
    address_1:     str
    address_2:     Optional[str] = None
    city:          Optional[str] = None
    state:         Optional[str] = None
    zip_code:      Optional[str] = None
    customer_type: str

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v):
        if not re.match(r"^[6-9]\d{9}$", v):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return v

    @field_validator("customer_type")
    @classmethod
    def validate_customer_type(cls, v):
        if v not in ["Individual", "Company"]:
            raise ValueError("customer_type must be Individual or Company")
        return v

GST_REGEX     = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
PINCODE_REGEX = r"^[1-9][0-9]{5}$"


class CompanyKYCCreate(BaseModel):
    company_name:          str
    company_type:          str
    gst_number:            str
    registered_address_1:  str
    registered_address_2:  Optional[str] = None
    registered_address_3:  Optional[str] = None
    city:                  str
    state:                 str
    pincode:               str
    contact_person_name:   str
    contact_person_mobile: str
    contact_person_email:  EmailStr
    customer_kyc_id: int

    @field_validator("company_type")
    @classmethod
    def validate_company_type(cls, v):
        if v not in ["Pvt Ltd", "LLP", "Partnership", "Limited"]:
            raise ValueError("company_type must be one of: Pvt Ltd, LLP, Partnership, Limited")
        return v

    @field_validator("gst_number")
    @classmethod
    def validate_gst(cls, v):
        if not re.match(GST_REGEX, v.upper()):
            raise ValueError("Enter a valid 15-character Indian GST number")
        return v.upper()

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v):
        if not re.match(PINCODE_REGEX, v):
            raise ValueError("Enter a valid 6-digit Indian pincode")
        return v

    @field_validator("contact_person_mobile")
    @classmethod
    def validate_mobile(cls, v):
        # mobile: 10 digits starting 6-9  |  landline: 11 digits starting with 0
        if not re.match(r"^([6-9]\d{9}|0[1-9]\d{9})$", v):
            raise ValueError("Enter a valid Indian mobile (10 digits) or landline number (e.g. 01140001234)")
        return v


class CompanyKYCResponse(BaseModel):
    id:                    int
    company_name:          str
    company_type:          str
    gst_number:            str
    city:                  str
    state:                 str
    contact_person_name:   str
    contact_person_mobile: str
    contact_person_email:  str
    incorporation_cert_url: Optional[str] = None
    gst_certificate_url:   Optional[str] = None
    status:          str
    customer_kyc_id: int

    class Config:
        from_attributes = True


class OwnerKYCCreate(BaseModel):
    first_name:    str
    middle_name:   Optional[str] = None
    last_name:     str
    date_of_birth: date
    mobile:        str
    email:         EmailStr
    company_name:  Optional[str] = None
    address_1:     str
    address_2:     Optional[str] = None
    city:          Optional[str] = None
    state:         Optional[str] = None
    zip_code:      Optional[str] = None

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v):
        if not re.match(r"^[6-9]\d{9}$", v):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return v


class OwnerKYCResponse(BaseModel):
    id:                  int
    first_name:          str
    last_name:           str
    mobile:              str
    email:               str
    company_name:        Optional[str] = None
    address_1:           str
    address_2:           Optional[str] = None
    city:                Optional[str] = None
    state:               Optional[str] = None
    zip_code:            Optional[str] = None
    driving_license_url: Optional[str] = None
    owner_id_url:        Optional[str] = None
    status:              str
    otp_verified:        str

    class Config:
        from_attributes = True


class OTPRequest(BaseModel):
    mobile: str
    email: Optional[str] = None 

class OTPVerify(BaseModel):
    mobile: str
    otp:    str

class KYCResponse(BaseModel):
    id:            int
    first_name:    str
    last_name:     str
    mobile:        str
    email:         str
    address_1:     str
    address_2:     Optional[str] = None
    city:          Optional[str] = None
    state:         Optional[str] = None
    zip_code:      Optional[str] = None
    customer_type: str
    status:        str
    otp_verified:  str

    class Config:
        from_attributes = True