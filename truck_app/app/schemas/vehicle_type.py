from pydantic import BaseModel, field_validator
from typing import Optional


class VehicleTypeCreate(BaseModel):
    type_name:          str
    description:        Optional[str] = None
    max_load_capacity:  Optional[float] = None
    dimensions:         Optional[str] = None

    @field_validator("type_name")
    @classmethod
    def validate_type_name(cls, v):
        if not v.strip():
            raise ValueError("type_name cannot be blank")
        return v.strip()

    @field_validator("max_load_capacity")
    @classmethod
    def validate_capacity(cls, v):
        if v is not None and v <= 0:
            raise ValueError("max_load_capacity must be greater than 0")
        return v


class VehicleTypeUpdate(BaseModel):
    type_name:          Optional[str] = None
    description:        Optional[str] = None
    max_load_capacity:  Optional[float] = None
    dimensions:         Optional[str] = None
    is_active:          Optional[bool] = None


class VehicleTypeResponse(BaseModel):
    id:                 int
    type_name:          str
    description:        Optional[str] = None
    max_load_capacity:  Optional[float] = None
    dimensions:         Optional[str] = None
    is_active:          bool

    class Config:
        from_attributes = True
