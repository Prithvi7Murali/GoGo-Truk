from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
import io
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.auth import get_current_admin
from app.utils.analytics import (
    booking_stats, revenue_stats, active_trucks,
    new_customers, top_routes, booking_trend, customer_growth,
    weekly_date_range, monthly_date_range,
)

router = APIRouter(prefix="/api/admin/analytics", tags=["Admin Analytics"])


def _resolve_range(period: str, date_from, date_to):
    if period == "weekly":
        return weekly_date_range()
    if period == "monthly":
        return monthly_date_range()
    if period == "last_7_days":
        today = date.today()
        return today - timedelta(days=6), today
    if period == "last_30_days":
        today = date.today()
        return today - timedelta(days=29), today
    if date_from and date_to:
        return date_from, date_to
    today = date.today()
    return today - timedelta(days=29), today


@router.get("/summary")
def summary(
    period: str = Query("last_30_days", description="weekly | monthly | last_7_days | last_30_days | custom"),
    date_from: date | None = Query(None),
    date_to:   date | None = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    from_dt, to_dt = _resolve_range(period, date_from, date_to)
    return {
        "period":       period,
        "from":         str(from_dt),
        "to":           str(to_dt),
        "bookings":     booking_stats(db, from_dt, to_dt),
        "revenue":      revenue_stats(db, from_dt, to_dt),
        "active_trucks": active_trucks(db),
        "new_customers": new_customers(db, from_dt, to_dt),
    }


@router.get("/top-routes")
def get_top_routes(
    period: str = Query("last_30_days"),
    date_from: date | None = Query(None),
    date_to:   date | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    from_dt, to_dt = _resolve_range(period, date_from, date_to)
    return {
        "from": str(from_dt),
        "to":   str(to_dt),
        "routes": top_routes(db, from_dt, to_dt, limit=limit),
    }


@router.get("/trend")
def get_trend(
    period: str = Query("last_30_days"),
    date_from: date | None = Query(None),
    date_to:   date | None = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    from_dt, to_dt = _resolve_range(period, date_from, date_to)
    return {
        "from":  str(from_dt),
        "to":    str(to_dt),
        "trend": booking_trend(db, from_dt, to_dt),
    }


@router.get("/customer-growth")
def get_customer_growth(
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    return {"growth": customer_growth(db, months=months)}


@router.post("/generate-report")
def generate_report_now(
    report_type: str = Query("weekly", description="weekly | monthly"),
    date_from: date | None = Query(None),
    date_to:   date | None = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    """Manually trigger report generation and email delivery."""
    from app.utils.scheduled_report import generate_report_pdf, generate_report_excel, email_report
    from_dt, to_dt = _resolve_range(report_type, date_from, date_to)
    pdf   = generate_report_pdf(db, from_dt, to_dt, report_type)
    excel = generate_report_excel(db, from_dt, to_dt, report_type)
    email_report(pdf, excel, report_type, from_dt, to_dt)
    return {
        "message":  f"{report_type.title()} report generated and emailed",
        "from":     str(from_dt),
        "to":       str(to_dt),
        "pdf_size": len(pdf),
        "excel_size": len(excel),
    }


@router.get("/download/report.pdf")
def download_report_pdf(
    report_type: str = Query("weekly"),
    date_from: date | None = Query(None),
    date_to:   date | None = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    from app.utils.scheduled_report import generate_report_pdf
    from_dt, to_dt = _resolve_range(report_type, date_from, date_to)
    pdf = generate_report_pdf(db, from_dt, to_dt, report_type)
    fname = f"gogotruk_{report_type}_report_{from_dt}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


@router.get("/download/report.xlsx")
def download_report_excel(
    report_type: str = Query("weekly"),
    date_from: date | None = Query(None),
    date_to:   date | None = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    from app.utils.scheduled_report import generate_report_excel
    from_dt, to_dt = _resolve_range(report_type, date_from, date_to)
    excel = generate_report_excel(db, from_dt, to_dt, report_type)
    fname = f"gogotruk_{report_type}_report_{from_dt}.xlsx"
    return StreamingResponse(
        io.BytesIO(excel),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )
