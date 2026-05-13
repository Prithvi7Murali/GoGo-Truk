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
        app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="Asia/Kolkata",
            enable_utc=True,
        )
        return app
    except ImportError:
        return None


celery_app = make_celery()
