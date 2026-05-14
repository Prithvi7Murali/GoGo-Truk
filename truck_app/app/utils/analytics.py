from datetime import date, datetime, timedelta, timezone
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.models.kyc import CustomerKYC
from app.models.fleet import Fleet
from app.models.booking import Booking
from app.models.invoice import Invoice
from app.models.availability import Availability


def booking_stats(db: Session, from_date: date, to_date: date) -> dict:
    q = db.query(Booking).filter(
        func.date(Booking.created_at) >= from_date,
        func.date(Booking.created_at) <= to_date,
    )
    total     = q.count()
    confirmed = q.filter(Booking.status == "Confirmed").count()
    completed = q.filter(Booking.status == "Completed").count()
    cancelled = q.filter(Booking.status == "Cancelled").count()
    rejected  = q.filter(Booking.status == "Rejected").count()
    pending   = q.filter(Booking.status == "Pending").count()
    return {
        "total": total,
        "confirmed": confirmed,
        "completed": completed,
        "cancelled": cancelled,
        "rejected": rejected,
        "pending": pending,
    }


def revenue_stats(db: Session, from_date: date, to_date: date) -> dict:
    rows = db.query(Invoice).filter(
        func.date(Invoice.created_at) >= from_date,
        func.date(Invoice.created_at) <= to_date,
    ).all()
    total_invoiced  = sum(r.total_amount for r in rows)
    total_collected = sum(r.total_amount for r in rows if r.status == "Sent")
    return {
        "total_invoiced":  round(total_invoiced, 2),
        "total_collected": round(total_collected, 2),
        "outstanding":     round(total_invoiced - total_collected, 2),
        "invoice_count":   len(rows),
    }


def active_trucks(db: Session) -> int:
    return db.query(func.count(func.distinct(Availability.fleet_id))).filter(
        Availability.status.in_(["Available", "Booked"])
    ).scalar() or 0


def new_customers(db: Session, from_date: date, to_date: date) -> int:
    return db.query(func.count(CustomerKYC.id)).filter(
        func.date(CustomerKYC.created_at) >= from_date,
        func.date(CustomerKYC.created_at) <= to_date,
    ).scalar() or 0


def top_routes(db: Session, from_date: date, to_date: date, limit: int = 10) -> list:
    rows = (
        db.query(
            Booking.pickup_address,
            Booking.destination_address,
            func.count(Booking.id).label("count"),
        )
        .filter(
            func.date(Booking.created_at) >= from_date,
            func.date(Booking.created_at) <= to_date,
        )
        .group_by(Booking.pickup_address, Booking.destination_address)
        .order_by(func.count(Booking.id).desc())
        .limit(limit)
        .all()
    )
    return [
        {"from": r.pickup_address, "to": r.destination_address, "bookings": r.count}
        for r in rows
    ]


def booking_trend(db: Session, from_date: date, to_date: date) -> list:
    """Daily booking count + revenue for each day in range."""
    rows = (
        db.query(
            func.date(Booking.created_at).label("day"),
            func.count(Booking.id).label("bookings"),
        )
        .filter(
            func.date(Booking.created_at) >= from_date,
            func.date(Booking.created_at) <= to_date,
        )
        .group_by(func.date(Booking.created_at))
        .order_by(func.date(Booking.created_at))
        .all()
    )
    rev_rows = (
        db.query(
            func.date(Invoice.created_at).label("day"),
            func.coalesce(func.sum(Invoice.total_amount), 0.0).label("revenue"),
        )
        .filter(
            func.date(Invoice.created_at) >= from_date,
            func.date(Invoice.created_at) <= to_date,
        )
        .group_by(func.date(Invoice.created_at))
        .all()
    )
    rev_map = {str(r.day): float(r.revenue) for r in rev_rows}
    return [
        {"date": str(r.day), "bookings": r.bookings, "revenue": rev_map.get(str(r.day), 0.0)}
        for r in rows
    ]


def customer_growth(db: Session, months: int = 6) -> list:
    """Monthly new customer count for the last N months."""
    result = []
    today = date.today()
    for i in range(months - 1, -1, -1):
        first = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        if first.month == 12:
            last = first.replace(year=first.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last = first.replace(month=first.month + 1, day=1) - timedelta(days=1)
        count = db.query(func.count(CustomerKYC.id)).filter(
            func.date(CustomerKYC.created_at) >= first,
            func.date(CustomerKYC.created_at) <= last,
        ).scalar() or 0
        result.append({"month": first.strftime("%b %Y"), "new_customers": count})
    return result


def weekly_date_range() -> tuple[date, date]:
    today = date.today()
    to_dt = today - timedelta(days=1)
    from_dt = to_dt - timedelta(days=6)
    return from_dt, to_dt


def monthly_date_range() -> tuple[date, date]:
    today = date.today()
    first_this_month = today.replace(day=1)
    last_month_end   = first_this_month - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    return last_month_start, last_month_end
