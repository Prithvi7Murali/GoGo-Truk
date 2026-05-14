from app.config import settings


def make_celery():
    if not settings.REDIS_URL:
        return None
    try:
        from celery import Celery
        app = Celery(
            "gogotruk",
            broker=settings.REDIS_URL,
            backend=settings.REDIS_URL,
            include=["app.tasks.booking_tasks"],
        )
        from celery.schedules import crontab
        app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="Asia/Kolkata",
            enable_utc=True,
            beat_schedule={
                "weekly-report": {
                    "task": "tasks.weekly_report",
                    "schedule": crontab(hour=8, minute=0, day_of_week="monday"),
                },
                "monthly-report": {
                    "task": "tasks.monthly_report",
                    "schedule": crontab(hour=8, minute=0, day_of_month="1"),
                },
            },
        )
        app.conf.include = ["app.tasks.booking_tasks", "app.tasks.report_tasks"]
        return app
    except ImportError:
        return None


celery_app = make_celery()
