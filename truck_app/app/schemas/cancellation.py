from pydantic import BaseModel, field_validator
from typing import Optional


class CancellationRequest(BaseModel):
    cancelled_by: str
    reason:       str

    @field_validator("cancelled_by")
    @classmethod
    def validate_cancelled_by(cls, v):
        if v not in ["Customer", "Owner"]:
            raise ValueError("cancelled_by must be Customer or Owner")
        return v

    @field_validator("reason")
    @classmethod
    def reason_not_blank(cls, v):
        if not v.strip():
            raise ValueError("reason cannot be blank")
        return v.strip()


class CancellationPreview(BaseModel):
    booking_id:                int
    booking_date:              str
    hours_before_pickup:       float
    cancellation_charge_pct:   float
    cancellation_charge_amount: float
    refund_amount:             float
    invoice_total:             Optional[float] = None


class CancellationResponse(BaseModel):
    id:                        int
    booking_id:                int
    cancelled_by:              str
    reason:                    str
    hours_before_pickup:       float
    cancellation_charge_pct:   float
    cancellation_charge_amount: float
    refund_amount:             float
    refund_status:             str

    class Config:
        from_attributes = True
