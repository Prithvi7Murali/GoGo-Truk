from pydantic import BaseModel, field_validator
from typing import Optional


class InvoiceCreate(BaseModel):
    booking_id:      int
    distance_km:     float
    waiting_charges: float = 0.0
    toll_charges:    float = 0.0
    loading_charges: float = 0.0
    gst_type:        str = "CGST+SGST"  # or "IGST"
    gst_rate:        float = 5.0        # total GST % (5 or 12 for freight)

    @field_validator("distance_km")
    @classmethod
    def distance_positive(cls, v):
        if v <= 0:
            raise ValueError("distance_km must be greater than 0")
        return v

    @field_validator("waiting_charges", "toll_charges", "loading_charges")
    @classmethod
    def charges_non_negative(cls, v):
        if v < 0:
            raise ValueError("Charges cannot be negative")
        return v

    @field_validator("gst_type")
    @classmethod
    def validate_gst_type(cls, v):
        if v not in ["CGST+SGST", "IGST"]:
            raise ValueError("gst_type must be CGST+SGST or IGST")
        return v

    @field_validator("gst_rate")
    @classmethod
    def validate_gst_rate(cls, v):
        if v not in [0, 5, 12, 18]:
            raise ValueError("gst_rate must be 0, 5, 12, or 18")
        return v


class PricingPreview(BaseModel):
    booking_id:      int
    distance_km:     float
    waiting_charges: float = 0.0
    toll_charges:    float = 0.0
    loading_charges: float = 0.0
    gst_type:        str = "CGST+SGST"
    gst_rate:        float = 5.0


class InvoiceResponse(BaseModel):
    id:               int
    invoice_number:   str
    booking_id:       int
    customer_kyc_id:  int
    distance_km:      float
    base_fare:        float
    waiting_charges:  float
    toll_charges:     float
    loading_charges:  float
    total_before_gst: float
    gst_type:         str
    cgst_rate:        float
    sgst_rate:        float
    igst_rate:        float
    cgst_amount:      float
    sgst_amount:      float
    igst_amount:      float
    total_amount:     float
    invoice_pdf_url:  Optional[str] = None
    status:           str

    class Config:
        from_attributes = True
