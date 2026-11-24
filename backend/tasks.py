"""Celery tasks.

Start the worker :  celery -A tasks.celery worker --loglevel=info        (add  -P solo  on Windows)
Start the beat   :  celery -A tasks.celery beat --loglevel=info
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery.schedules import crontab  # noqa: E402

from config import Config  # noqa: E402
from extensions import celery  # noqa: E402


class ContextTask(celery.Task):
    """Runs every task inside a Flask app context so SQLAlchemy works."""

    def __call__(self, *args, **kwargs):
        from app import get_flask_app
        with get_flask_app().app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask


@celery.task(name="tasks.daily_reminders")
def daily_reminders():
    import services
    return f"{services.send_daily_reminders()} reminders sent"


@celery.task(name="tasks.monthly_report")
def monthly_report(year=None, month=None):
    import services
    return services.send_monthly_report(year, month)


@celery.task(name="tasks.export_bookings")
def export_bookings(job_id):
    import services
    return services.export_booking_history(job_id)


celery.conf.beat_schedule = {
    "daily-reminders": {
        "task": "tasks.daily_reminders",
        "schedule": crontab(hour=Config.REMINDER_HOUR, minute=Config.REMINDER_MINUTE),
    },
    "monthly-report": {
        "task": "tasks.monthly_report",
        "schedule": crontab(day_of_month=1, hour=7, minute=0),
    },
}
