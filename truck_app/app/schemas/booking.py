from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional


class BookingCreate(BaseModel):
    customer_kyc_id:     int
    availability_id:     int
    pickup_address:      str
    destination_address: str
    goods_type:          str
    goods_weight_kg:     float
    declaration_accepted: bool

    @field_validator("goods_weight_kg")
    @classmethod
    def validate_weight(cls, v):
        if v <= 0:
            raise ValueError("Goods weight must be greater than 0")
        return v

    @field_validator("declaration_accepted")
    @classmethod
    def must_accept(cls, v):
        if not v:
            raise ValueError("Declaration must be accepted to submit a booking")
        return v

    @field_validator("pickup_address", "destination_address", "goods_type")
    @classmethod
    def not_blank(cls, v):
        if not v.strip():
            raise ValueError("Cannot be blank")
        return v.strip()


class BookingReview(BaseModel):
    action: str
    reason: Optional[str] = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if v not in ["Confirmed", "Rejected"]:
            raise ValueError("action must be Confirmed or Rejected")
        return v

    @field_validator("reason")
    @classmethod
    def reason_required_for_rejection(cls, v, info):
        if info.data.get("action") == "Rejected" and not (v and v.strip()):
            raise ValueError("reason is required when rejecting a booking")
        return v.strip() if v else v


class BookingResponse(BaseModel):
    id:                      int
    customer_kyc_id:         int
    availability_id:         int
    fleet_id:                int
    pickup_address:          str
    destination_address:     str
    booking_date:            date
    goods_type:              str
    goods_weight_kg:         float
    declaration_accepted:    bool
    status:                  str
    rejection_reason:        Optional[str] = None
    owner_response_deadline: Optional[datetime] = None

    class Config:
        from_attributes = True
