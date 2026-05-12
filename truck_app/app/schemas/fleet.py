from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date
import re

REG_NUMBER_REGEX = r"^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$"


class FleetCreate(BaseModel):
    owner_kyc_id:        int
    vehicle_type:        str
    description:         Optional[str] = None
    max_load_capacity:   Optional[float] = None
    dimensions:          Optional[str] = None
    registration_number: str
    engine_number:       str
    chassis_number:      str

    @field_validator("registration_number")
    @classmethod
    def validate_registration_number(cls, v):
        cleaned = v.upper().replace(" ", "")
        if not re.match(REG_NUMBER_REGEX, cleaned):
            raise ValueError("Enter a valid Indian registration number (e.g. MH12AB1234)")
        return cleaned

    @field_validator("engine_number", "chassis_number")
    @classmethod
    def validate_alphanumeric(cls, v):
        if not v.strip():
            raise ValueError("Cannot be blank")
        return v.strip().upper()

    @field_validator("vehicle_type")
    @classmethod
    def validate_vehicle_type(cls, v):
        if not v.strip():
            raise ValueError("vehicle_type cannot be blank")
        return v.strip()


class FleetExpiryUpdate(BaseModel):
    rc_expiry_date:        Optional[date] = None
    insurance_expiry_date: Optional[date] = None
    permit_expiry_date:    Optional[date] = None
    puc_expiry_date:       Optional[date] = None


class FleetResponse(BaseModel):
    id:                    int
    owner_kyc_id:          int
    vehicle_type:          str
    description:           Optional[str] = None
    max_load_capacity:     Optional[float] = None
    dimensions:            Optional[str] = None
    registration_number:   str
    engine_number:         str
    chassis_number:        str
    rc_book_url:           Optional[str] = None
    rc_expiry_date:        Optional[date] = None
    insurance_url:         Optional[str] = None
    insurance_expiry_date: Optional[date] = None
    permit_url:            Optional[str] = None
    permit_expiry_date:    Optional[date] = None
    puc_url:               Optional[str] = None
    puc_expiry_date:       Optional[date] = None
    is_active:             bool

    class Config:
        from_attributes = True
