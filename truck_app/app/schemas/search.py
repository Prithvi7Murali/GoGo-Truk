from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class TruckSearchResult(BaseModel):
    availability_id:   int
    fleet_id:          int
    date:              date
    city:              str
    state:             str
    vehicle_type:      str
    description:       Optional[str] = None
    max_load_capacity: Optional[float] = None
    dimensions:        Optional[str] = None
    registration_number: str
    owner_kyc_id:      int
    owner_name:        str
    owner_mobile:      str
    owner_company:     Optional[str] = None


class SearchResponse(BaseModel):
    results:     List[TruckSearchResult]
    total:       int
    page:        int
    page_size:   int
    total_pages: int
