import re
from datetime import date
from functools import wraps

from flask import current_app, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from extensions import db
from models import User


def err(message, code=400):
    return jsonify({"error": message}), code


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="trek-auth")


def make_token(user):
    return _serializer().dumps({"id": user.id, "role": user.role})


def auth_required(*roles):
    """Role based access control. Usage: @auth_required('admin')"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                return err("Authentication required", 401)
            try:
                data = _serializer().loads(header[7:], max_age=current_app.config["TOKEN_MAX_AGE"])
            except SignatureExpired:
                return err("Session expired, please log in again", 401)
            except BadSignature:
                return err("Invalid token", 401)
            user = db.session.get(User, data["id"])
            if not user:
                return err("User no longer exists", 401)
            if user.status != "active":
                return err(f"Your account is {user.status}. Contact the admin.", 401)
            if roles and user.role not in roles:
                return err("You do not have access to this resource", 403)
            g.user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def valid_email(value):
    return bool(value) and bool(EMAIL_RE.match(value))


def valid_contact(value):
    digits = re.sub(r"[\s+-]", "", value or "")
    return digits.isdigit() and 7 <= len(digits) <= 15


def parse_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None
