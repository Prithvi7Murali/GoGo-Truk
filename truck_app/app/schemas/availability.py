from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import date as date_type


class AvailabilityCreate(BaseModel):
    fleet_id: int
    dates:    List[date_type]
    city:     str
    state:    str

    @field_validator("dates")
    @classmethod
    def validate_dates(cls, v):
        if not v:
            raise ValueError("At least one date must be provided")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate dates in the same request")
        if any(d < date_type.today() for d in v):
            raise ValueError("Dates cannot be in the past")
        return v

    @field_validator("city", "state")
    @classmethod
    def not_blank(cls, v):
        if not v.strip():
            raise ValueError("Cannot be blank")
        return v.strip()


class BookRequest(BaseModel):
    customer_kyc_id: int


class AvailabilityUpdate(BaseModel):
    date:   Optional[date_type] = None
    city:   Optional[str] = None
    state:  Optional[str] = None
    status: Optional[str] = None

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        if v is not None and v < date_type.today():
            raise ValueError("Date cannot be in the past")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in ["Available", "Booked", "Cancelled"]:
            raise ValueError("status must be Available, Booked, or Cancelled")
        return v


class AvailabilityResponse(BaseModel):
    id:       int
    fleet_id: int
    date:     date_type
    city:     str
    state:    str
    status:   str

    class Config:
        from_attributes = True
