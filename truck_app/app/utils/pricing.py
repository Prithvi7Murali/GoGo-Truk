from sqlalchemy.orm import Session
from app.models.rate_card import RateCard


def get_applicable_rate(db: Session, vehicle_type: str, distance_km: float) -> RateCard | None:
    cards = (
        db.query(RateCard)
        .filter(
            RateCard.vehicle_type == vehicle_type,
            RateCard.is_active == True,
            RateCard.distance_from_km <= distance_km,
        )
        .order_by(RateCard.distance_from_km.desc())
        .all()
    )
    for card in cards:
        if card.distance_to_km is None or distance_km <= card.distance_to_km:
            return card
    return None


def calculate_fare(rate: RateCard, distance_km: float) -> float:
    calculated = distance_km * rate.rate_per_km
    return max(calculated, rate.base_fare)


def calculate_gst(total_before_gst: float, gst_type: str, gst_rate: float) -> dict:
    if gst_type == "IGST":
        igst = round(total_before_gst * gst_rate / 100, 2)
        return {"cgst_rate": 0, "sgst_rate": 0, "igst_rate": gst_rate,
                "cgst_amount": 0.0, "sgst_amount": 0.0, "igst_amount": igst}
    else:
        half = gst_rate / 2
        cgst = round(total_before_gst * half / 100, 2)
        sgst = round(total_before_gst * half / 100, 2)
        return {"cgst_rate": half, "sgst_rate": half, "igst_rate": 0,
                "cgst_amount": cgst, "sgst_amount": sgst, "igst_amount": 0.0}
