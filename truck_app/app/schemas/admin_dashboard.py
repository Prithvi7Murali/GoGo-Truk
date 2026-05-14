from pydantic import BaseModel
from datetime import datetime


class KYCStats(BaseModel):
    pending: int
    verified: int
    rejected: int
    total: int


class BookingStats(BaseModel):
    pending: int
    confirmed: int
    completed: int
    cancelled: int
    rejected: int
    total: int


class RevenueStats(BaseModel):
    total_invoiced: float
    total_paid: float
    total_outstanding: float
    invoice_count: int


class FleetStats(BaseModel):
    total: int
    active: int
    inactive: int


class DashboardMetrics(BaseModel):
    kyc: KYCStats
    bookings: BookingStats
    revenue: RevenueStats
    fleet: FleetStats


class KYCQueueItem(BaseModel):
    id: int
    full_name: str
    customer_type: str
    mobile: str
    status: str
    submitted_at: datetime | None

    model_config = {"from_attributes": True}


class BookingOverviewItem(BaseModel):
    id: int
    customer_name: str
    owner_name: str
    vehicle_number: str
    pickup_location: str
    drop_location: str
    pickup_date: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RevenueReportItem(BaseModel):
    invoice_id: int
    invoice_number: str
    booking_id: int
    customer_name: str
    total_amount: float
    status: str
    generated_at: datetime

    model_config = {"from_attributes": True}
