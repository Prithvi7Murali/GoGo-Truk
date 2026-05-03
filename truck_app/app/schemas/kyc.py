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
    address_3:     Optional[str] = None
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

class OTPRequest(BaseModel):
    mobile: str

class OTPVerify(BaseModel):
    mobile: str
    otp:    str

class KYCResponse(BaseModel):
    id:           int
    first_name:   str
    last_name:    str
    mobile:       str
    email:        str
    status:       str
    otp_verified: str

    class Config:
        from_attributes = True