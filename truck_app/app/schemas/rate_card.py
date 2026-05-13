from pydantic import BaseModel, field_validator
from typing import Optional


class RateCardCreate(BaseModel):
    vehicle_type:     str
    distance_from_km: float
    distance_to_km:   Optional[float] = None
    base_fare:        float
    rate_per_km:      float

    @field_validator("distance_from_km", "base_fare", "rate_per_km")
    @classmethod
    def must_be_positive(cls, v):
        if v < 0:
            raise ValueError("Value must be >= 0")
        return v

    @field_validator("distance_to_km")
    @classmethod
    def to_must_exceed_from(cls, v, info):
        if v is not None and v <= info.data.get("distance_from_km", 0):
            raise ValueError("distance_to_km must be greater than distance_from_km")
        return v


class RateCardUpdate(BaseModel):
    base_fare:   Optional[float] = None
    rate_per_km: Optional[float] = None
    is_active:   Optional[bool] = None


class RateCardResponse(BaseModel):
    id:               int
    vehicle_type:     str
    distance_from_km: float
    distance_to_km:   Optional[float] = None
    base_fare:        float
    rate_per_km:      float
    is_active:        bool

    class Config:
        from_attributes = True
