from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ConsentSubmit(BaseModel):
    customer_kyc_id: int
    accepted: bool


class ConsentResponse(BaseModel):
    id:                  int
    customer_kyc_id:     int
    accepted:            bool
    declaration_version: str
    ip_address:          str
    device_info:         Optional[str] = None
    pdf_url:             Optional[str] = None
    timestamp:           Optional[datetime] = None

    class Config:
        from_attributes = True
