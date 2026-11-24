"""Central configuration. Every value can be overridden with an environment variable."""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-in-production")
    TOKEN_MAX_AGE = 60 * 60 * 12

    DB_DIR = os.path.join(BASE_DIR, "instance")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(DB_DIR, "trekking.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_CACHE_URL = os.getenv("REDIS_CACHE_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    CACHE_TTL = int(os.getenv("CACHE_TTL", "60"))

    ADMIN_NAME = os.getenv("ADMIN_NAME", "Super Admin")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@trek.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

    REMINDER_HOUR = int(os.getenv("REMINDER_HOUR", "8"))
    REMINDER_MINUTE = int(os.getenv("REMINDER_MINUTE", "0"))
    REMINDER_DAYS_AHEAD = int(os.getenv("REMINDER_DAYS_AHEAD", "7"))
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASS = os.getenv("SMTP_PASS", "")
    MAIL_FROM = os.getenv("MAIL_FROM", "no-reply@trekking.local")
    GCHAT_WEBHOOK_URL = os.getenv("GCHAT_WEBHOOK_URL", "")

    EXPORT_DIR = os.path.join(BASE_DIR, "exports")
    OUTBOX_DIR = os.path.join(BASE_DIR, "outbox")
