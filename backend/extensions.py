"""Shared objects (database and celery) so that no module imports the app itself."""
from celery import Celery
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()

celery = Celery(
    "trekking",
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
)
celery.conf.update(timezone=Config.TIMEZONE, enable_utc=True, broker_connection_retry_on_startup=True)
