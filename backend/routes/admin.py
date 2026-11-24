from datetime import datetime, timedelta

from flask import Blueprint, g, jsonify, request
from sqlalchemy import desc, func, or_

from cache import cache_clear_treks, redis_available
from extensions import db
from models import Booking, Trek, User, notify
from .utils import auth_required, err, parse_date, valid_contact, valid_email

bp = Blueprint("admin", __name__, url_prefix="/api/admin")

DIFFICULTIES = ("Easy", "Moderate", "Hard")
TREK_STATUSES = ("Pending", "Approved", "Open", "Closed", "Ongoing", "Completed")


@bp.get("/stats")
@auth_required("admin")
def stats():
    recent = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()
    return jsonify({
        "total_treks": Trek.query.count(),
        "total_users": User.query.filter_by(role="user").count(),
        "total_staff": User.query.filter_by(role="staff").count(),
        "total_bookings": Booking.query.count(),
        "active_bookings": Booking.query.filter_by(status="Booked").count(),
        "completed_treks": Trek.query.filter_by(status="Completed").count(),
        "recent_bookings": [b.to_dict() for b in recent],
    })


@bp.get("/analytics")
@auth_required("admin")
def analytics():
    live = Booking.status != "Cancelled"
    popular = (db.session.query(Trek.name, func.count(Booking.id)).join(Booking)
               .filter(live).group_by(Trek.id).order_by(desc(func.count(Booking.id))).limit(6).all())
    since = datetime.utcnow() - timedelta(days=180)
    monthly = (db.session.query(func.strftime("%Y-%m", Booking.booking_date), func.count(Booking.id))
               .filter(live, Booking.booking_date >= since)
               .group_by(func.strftime("%Y-%m", Booking.booking_date)).order_by(func.strftime("%Y-%m", Booking.booking_date)).all())
    by_status = db.session.query(Trek.status, func.count(Trek.id)).group_by(Trek.status).all()
    by_diff = (db.session.query(Trek.difficulty, func.count(Booking.id)).join(Booking)
               .filter(live).group_by(Trek.difficulty).all())
    top_users = (db.session.query(User.name, func.count(Booking.id)).join(Booking)
                 .filter(live).group_by(User.id).order_by(desc(func.count(Booking.id))).limit(5).all())
    return jsonify({
        "popular_treks": [{"name": n, "bookings": c} for n, c in popular],
        "monthly_bookings": [{"month": m, "bookings": c} for m, c in monthly],
        "trek_status": [{"status": s, "count": c} for s, c in by_status],
        "difficulty_bookings": [{"difficulty": d, "bookings": c} for d, c in by_diff],
        "top_users": [{"name": n, "bookings": c} for n, c in top_users],
    })


@bp.get("/report/preview")
@auth_required("admin")
def report_preview():
    import services
    today = datetime.utcnow()
    y, m = request.args.get("year", type=int) or today.year, request.args.get("month", type=int) or today.month
    d = services.report_data(y, m)
    d["html"] = services.render_report_html(d)
    return jsonify(d)


@bp.post("/report/send")
@auth_required("admin")
def report_send():
    d = request.get_json(silent=True) or {}
    year, month = d.get("year"), d.get("month")
    if redis_available():
        from tasks import monthly_report
        monthly_report.delay(year, month)
        return jsonify({"message": "Report job queued. Check the admin mailbox / outbox shortly."})
    import services
    label = services.send_monthly_report(year, month)
    return jsonify({"message": f"Redis is offline, report for {label} generated directly."})


def _clean_trek(d, trek=None):
    get = lambda k: d.get(k, getattr(trek, k, None) if trek else None)
    name, location = (get("name") or "").strip(), (get("location") or "").strip()
    if len(name) < 3:
        return None, "Trek name must be at least 3 characters"
    if not location:
        return None, "Location is required"
    if get("difficulty") not in DIFFICULTIES:
        return None, "Difficulty must be Easy, Moderate or Hard"
    try:
        duration, slots = int(get("duration_days")), int(get("total_slots"))
    except (TypeError, ValueError):
        return None, "Duration and slots must be numbers"
    if duration < 1 or duration > 60:
        return None, "Duration must be between 1 and 60 days"
    if slots < 1:
        return None, "Slots must be at least 1"
    start = parse_date(get("start_date")) if isinstance(get("start_date"), str) else get("start_date")
    if not start:
        return None, "A valid start date is required"
    status = get("status") or "Pending"
    if status not in TREK_STATUSES:
        return None, "Invalid status"
    values = dict(
        name=name,
        location=location,
        difficulty=get("difficulty"),
        duration_days=duration,
        total_slots=slots,
        start_date=start,
        end_date=start + timedelta(days=duration - 1),
        status=status,
        altitude_m=get("altitude_m") or None,
        description=get("description"),
        instructions=get("instructions"),
    )
    return values, None


def _check_staff(staff_id):
    if staff_id in (None, "", 0):
        return None, None
    staff = db.session.get(User, int(staff_id))
    if not staff or staff.role != "staff" or staff.status != "active":
        return None, "Selected staff member is not available"
    return staff, None


@bp.get("/treks")
@auth_required("admin")
def list_treks():
    q, status = (request.args.get("q") or "").strip(), request.args.get("status")
    query = Trek.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Trek.name.ilike(like), Trek.location.ilike(like)))
    if status:
        query = query.filter_by(status=status)
    return jsonify([t.to_dict() for t in query.order_by(Trek.start_date.desc()).all()])


@bp.post("/treks")
@auth_required("admin")
def create_trek():
    d = request.get_json(silent=True) or {}
    values, error = _clean_trek(d)
    if error:
        return err(error)
    staff, error = _check_staff(d.get("staff_id"))
    if error:
        return err(error)
    trek = Trek(**values, available_slots=values["total_slots"], staff_id=staff.id if staff else None)
    db.session.add(trek)
    db.session.commit()
    cache_clear_treks()
    return jsonify(trek.to_dict()), 201


@bp.put("/treks/<int:trek_id>")
@auth_required("admin")
def update_trek(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek:
        return err("Trek not found", 404)
    d = request.get_json(silent=True) or {}
    values, error = _clean_trek(d, trek)
    if error:
        return err(error)
    booked = trek.total_slots - trek.available_slots
    if values["total_slots"] < booked:
        return err(f"Cannot set slots below the {booked} already booked")
    if "staff_id" in d:
        staff, error = _check_staff(d.get("staff_id"))
        if error:
            return err(error)
        trek.staff_id = staff.id if staff else None
    for key, value in values.items():
        setattr(trek, key, value)
    trek.available_slots = trek.total_slots - booked
    db.session.commit()
    cache_clear_treks()
    return jsonify(trek.to_dict())


@bp.put("/treks/<int:trek_id>/assign")
@auth_required("admin")
def assign_staff(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek:
        return err("Trek not found", 404)
    staff, error = _check_staff((request.get_json(silent=True) or {}).get("staff_id"))
    if error:
        return err(error)
    trek.staff_id = staff.id if staff else None
    if staff:
        notify(staff.id, f"You have been assigned to trek '{trek.name}'.", "info")
    db.session.commit()
    cache_clear_treks()
    return jsonify(trek.to_dict())


@bp.delete("/treks/<int:trek_id>")
@auth_required("admin")
def delete_trek(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek:
        return err("Trek not found", 404)
    if Booking.query.filter_by(trek_id=trek.id).count():
        return err("This trek has booking history and cannot be deleted. Set its status to Closed instead.", 409)
    db.session.delete(trek)
    db.session.commit()
    cache_clear_treks()
    return jsonify({"message": "Trek deleted"})

@bp.get("/staff")
@auth_required("admin")
def list_staff():
    q = (request.args.get("q") or "").strip()
    query = User.query.filter_by(role="staff")
    if q:
        like = f"%{q}%"
        query = query.filter(or_(User.name.ilike(like), User.email.ilike(like)))
    return jsonify([u.to_dict() for u in query.order_by(User.id.desc()).all()])


@bp.post("/staff")
@auth_required("admin")
def create_staff():
    d = request.get_json(silent=True) or {}
    name = (d.get("name") or "").strip()
    email = (d.get("email") or "").strip().lower()
    contact = (d.get("contact") or "").strip()
    password = d.get("password") or ""
    if len(name) < 2:
        return err("Name must be at least 2 characters")
    if not valid_email(email):
        return err("Enter a valid email address")
    if contact and not valid_contact(contact):
        return err("Enter a valid contact number")
    if len(password) < 6:
        return err("Password must be at least 6 characters")
    if User.query.filter_by(email=email).first():
        return err("An account with this email already exists", 409)
    staff = User(
        name=name,
        email=email,
        contact=contact,
        role="staff",
        status="active",
        experience_years=int(d.get("experience_years") or 0),
        specialization=(d.get("specialization") or "").strip(),
    )
    staff.set_password(password)
    db.session.add(staff)
    db.session.commit()
    return jsonify(staff.to_dict()), 201

@bp.put("/staff/<int:staff_id>")
@auth_required("admin")
def update_staff(staff_id):
    staff = User.query.filter_by(id=staff_id, role="staff").first()
    if not staff:
        return err("Staff member not found", 404)
    d = request.get_json(silent=True) or {}
    if "name" in d:
        if len((d["name"] or "").strip()) < 2:
            return err("Name must be at least 2 characters")
    staff.name = d["name"].strip()
    if "contact" in d:
        if d["contact"] and not valid_contact(d["contact"]):
            return err("Enter a valid contact number")
        staff.contact = (d["contact"] or "").strip()
    if "experience_years" in d:
        staff.experience_years = int(d["experience_years"] or 0)
    if "specialization" in d:
        staff.specialization = (d["specialization"] or "").strip()
    if d.get("password"):
        if len(d["password"]) < 6:
            return err("Password must be at least 6 characters")
        staff.set_password(d["password"])
    db.session.commit()
    return jsonify(staff.to_dict())


@bp.delete("/staff/<int:staff_id>")
@auth_required("admin")
def delete_staff(staff_id):
    staff = User.query.filter_by(id=staff_id, role="staff").first()
    if not staff:
        return err("Staff member not found", 404)
    for t in Trek.query.filter_by(staff_id=staff.id).all():
        t.staff_id = None
    db.session.delete(staff)
    db.session.commit()
    cache_clear_treks()
    return jsonify({"message": "Staff removed"})


@bp.get("/users")
@auth_required("admin")
def list_users():
    q = (request.args.get("q") or "").strip()
    query = User.query.filter_by(role="user")
    if q:
        like = f"%{q}%"
        query = query.filter(or_(User.name.ilike(like), User.email.ilike(like)))
    return jsonify([u.to_dict() for u in query.order_by(User.id.desc()).all()])


@bp.put("/users/<int:user_id>/status")
@auth_required("admin")
def update_user_status(user_id):
    user = db.session.get(User, user_id)
    if not user or user.role == "admin":
        return err("User not found", 404)
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in ("active", "inactive", "blacklisted"):
        return err("Invalid status")
    user.status = status
    db.session.commit()
    return jsonify(user.to_dict())


@bp.get("/bookings")
@auth_required("admin")
def list_bookings():
    q = (request.args.get("q") or "").strip()
    query = Booking.query.join(User).join(Trek)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(User.name.ilike(like), User.email.ilike(like), Trek.name.ilike(like)))
    return jsonify([b.to_dict() for b in query.order_by(Booking.booking_date.desc()).all()])
