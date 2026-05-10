from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app.utils.expiry_checker import check_fleet_expiry

_scheduler = BackgroundScheduler()


def _run():
    db = SessionLocal()
    try:
        check_fleet_expiry(db)
    finally:
        db.close()


def start_scheduler():
    _scheduler.add_job(_run, "cron", hour=8, minute=0, id="expiry_check", replace_existing=True)
    _scheduler.start()
    print("[scheduler] Expiry check job scheduled — runs daily at 08:00")


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
