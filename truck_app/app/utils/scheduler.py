from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app.utils.expiry_checker import check_fleet_expiry

_scheduler = BackgroundScheduler()


def _run_expiry_check():
    db = SessionLocal()
    try:
        check_fleet_expiry(db)
    finally:
        db.close()


def _run_auto_reject():
    from datetime import datetime, timezone
    from app.models.booking import Booking, BookingStatus
    from app.tasks.booking_tasks import _auto_reject_booking

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        expired = (
            db.query(Booking)
            .filter(
                Booking.status == "Pending",
                Booking.owner_response_deadline <= now,
            )
            .all()
        )
        for b in expired:
            _auto_reject_booking(b.id)
    finally:
        db.close()


def _run_weekly_report():
    from app.tasks.report_tasks import run_weekly_report
    run_weekly_report()


def _run_monthly_report():
    from app.tasks.report_tasks import run_monthly_report
    run_monthly_report()


def start_scheduler():
    _scheduler.add_job(_run_expiry_check,  "cron",     hour=8, minute=0, id="expiry_check",   replace_existing=True)
    _scheduler.add_job(_run_auto_reject,   "interval", minutes=10,        id="auto_reject",    replace_existing=True)
    _scheduler.add_job(_run_weekly_report, "cron",     day_of_week="mon", hour=8, minute=0, id="weekly_report",  replace_existing=True)
    _scheduler.add_job(_run_monthly_report,"cron",     day=1,             hour=8, minute=0, id="monthly_report", replace_existing=True)
    _scheduler.start()
    print("[scheduler] Expiry check    — daily at 08:00")
    print("[scheduler] Auto-reject     — every 10 minutes")
    print("[scheduler] Weekly report   — every Monday at 08:00")
    print("[scheduler] Monthly report  — 1st of every month at 08:00")


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
