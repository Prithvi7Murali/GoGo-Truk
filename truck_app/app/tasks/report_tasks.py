from app.database import SessionLocal
from app.utils.analytics import weekly_date_range, monthly_date_range
from app.utils.scheduled_report import generate_report_pdf, generate_report_excel, email_report


def _run_report(report_type: str):
    from_date, to_date = weekly_date_range() if report_type == "weekly" else monthly_date_range()
    db = SessionLocal()
    try:
        print(f"[report] Generating {report_type} report: {from_date} → {to_date}")
        pdf   = generate_report_pdf(db, from_date, to_date, report_type)
        excel = generate_report_excel(db, from_date, to_date, report_type)
        email_report(pdf, excel, report_type, from_date, to_date)
    except Exception as e:
        print(f"[report] {report_type} report failed: {e}")
    finally:
        db.close()


def run_weekly_report():
    _run_report("weekly")


def run_monthly_report():
    _run_report("monthly")


# ── Celery tasks (only registered when Redis is available) ────────────────────

from app.celery_app import celery_app

if celery_app:
    @celery_app.task(name="tasks.weekly_report")
    def weekly_report_task():
        run_weekly_report()

    @celery_app.task(name="tasks.monthly_report")
    def monthly_report_task():
        run_monthly_report()
