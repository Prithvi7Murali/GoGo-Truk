from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class KYCReviewAction(BaseModel):
    status: str   # "Verified" or "Rejected"
    reason: Optional[str] = None

    def validate_action(self):
        if self.status not in ["Verified", "Rejected"]:
            raise ValueError("status must be 'Verified' or 'Rejected'")
        if self.status == "Rejected" and not self.reason:
            raise ValueError("reason is required when rejecting")


class PendingKYCItem(BaseModel):
    id:         int
    kyc_type:   str   # "Customer", "Company", "Owner"
    name:       str
    mobile:     str
    email:      str
    status:     str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
