import threading
from datetime import datetime

from flask import Blueprint, current_app, g, jsonify, request, send_file
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from cache import cache_clear_treks, cache_get, cache_set, redis_available
from extensions import db
from models import Booking, ExportJob, Notification, Trek, notify
from .utils import auth_required, err

bp = Blueprint("user", __name__, url_prefix="/api")

VISIBLE = ("Approved", "Open", "Closed")


def _cached_json(key, builder):
    data = cache_get(key)
    hit = data is not None
    if not hit:
        data = builder()
        cache_set(key, data)
    resp = jsonify(data)
    resp.headers["X-Cache"] = "HIT" if hit else "MISS"
    return resp


@bp.get("/treks")
@auth_required()
def browse_treks():
    a = request.args
    key = "treks:list:" + "&".join(f"{k}={a.get(k, '')}" for k in
                                   ("q", "difficulty", "location", "min_days", "max_days", "status"))

    def build():
        query = Trek.query.filter(Trek.status.in_(VISIBLE))
        if a.get("q"):
            like = f"%{a['q'].strip()}%"
            query = query.filter(Trek.name.ilike(like) | Trek.location.ilike(like))
        if a.get("difficulty") in ("Easy", "Moderate", "Hard"):
            query = query.filter(Trek.difficulty == a["difficulty"])
        if a.get("location"):
            query = query.filter(Trek.location.ilike(f"%{a['location'].strip()}%"))
        if a.get("min_days", type=int):
            query = query.filter(Trek.duration_days >= a.get("min_days", type=int))
        if a.get("max_days", type=int):
            query = query.filter(Trek.duration_days <= a.get("max_days", type=int))
        if a.get("status") in VISIBLE:
            query = query.filter(Trek.status == a["status"])
        return [t.to_dict() for t in query.order_by(Trek.start_date).all()]

    return _cached_json(key, build)


@bp.get("/treks/locations")
@auth_required()
def locations():
    return _cached_json("treks:locations", lambda: sorted(
        {t.location for t in Trek.query.filter(Trek.status.in_(VISIBLE))}))


@bp.get("/treks/<int:trek_id>")
@auth_required()
def trek_detail(trek_id):
    resp = _cached_json(f"trek:{trek_id}", lambda: (
        lambda t: t.to_dict() if t and t.status in VISIBLE + ("Ongoing", "Completed") else None)(db.session.get(Trek, trek_id)))
    return resp if resp.get_json() else err("Trek not found", 404)


@bp.post("/treks/<int:trek_id>/book")
@auth_required("user")
def book(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek or trek.status not in VISIBLE:
        return err("Trek not found", 404)
    if trek.status != "Open":
        return err("Bookings are only allowed while the trek is Open", 409)
    if Booking.query.filter_by(user_id=g.user.id, trek_id=trek.id, status="Booked").first():
        return err("You have already booked this trek", 409)

    taken = db.session.execute(
        update(Trek).where(Trek.id == trek.id, Trek.status == "Open", Trek.available_slots > 0)
        .values(available_slots=Trek.available_slots - 1))
    if taken.rowcount == 0:
        db.session.rollback()
        return err("Sorry, no slots left for this trek", 409)
    booking = Booking(user_id=g.user.id, trek_id=trek.id)
    db.session.add(booking)
    notify(g.user.id, f"Booking confirmed for '{trek.name}' starting {trek.start_date:%d %b %Y}.", "success")
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return err("You have already booked this trek", 409)
    cache_clear_treks()
    return jsonify({"message": "Booking confirmed", "booking": booking.to_dict()}), 201


@bp.get("/bookings")
@auth_required("user")
def my_bookings():
    rows = Booking.query.filter_by(user_id=g.user.id).order_by(Booking.booking_date.desc()).all()
    return jsonify([b.to_dict() for b in rows])


@bp.post("/bookings/<int:booking_id>/cancel")
@auth_required("user")
def cancel(booking_id):
    b = Booking.query.filter_by(id=booking_id, user_id=g.user.id).first()
    if not b:
        return err("Booking not found", 404)
    if b.status != "Booked":
        return err(f"A {b.status.lower()} booking cannot be cancelled", 409)
    if b.trek.status in ("Ongoing", "Completed"):
        return err("This trek has already started", 409)
    b.status, b.cancelled_at = "Cancelled", datetime.utcnow()
    b.trek.available_slots += 1
    notify(g.user.id, f"Your booking for '{b.trek.name}' has been cancelled.", "warning")
    db.session.commit()
    cache_clear_treks()
    return jsonify({"message": "Booking cancelled"})


@bp.get("/history")
@auth_required("user")
def history():
    rows = (Booking.query.filter(Booking.user_id == g.user.id, Booking.status.in_(["Completed", "Cancelled"]))
            .order_by(Booking.booking_date.desc()).all())
    return jsonify([b.to_dict() for b in rows])


@bp.get("/dashboard")
@auth_required("user")
def dashboard():
    mine = Booking.query.filter_by(user_id=g.user.id).all()
    return jsonify({
        "booked": sum(b.status == "Booked" for b in mine),
        "completed": sum(b.status == "Completed" for b in mine),
        "cancelled": sum(b.status == "Cancelled" for b in mine),
        "upcoming": [b.to_dict() for b in mine if b.status == "Booked"][:5],
    })


@bp.post("/export")
@auth_required("user")
def start_export():
    job = ExportJob(user_id=g.user.id)
    db.session.add(job)
    db.session.commit()
    if redis_available():
        from tasks import export_bookings
        export_bookings.delay(job.id)
    else:
        app, job_id = current_app._get_current_object(), job.id

        def run():
            import services
            with app.app_context():
                services.export_booking_history(job_id)
        threading.Thread(target=run, daemon=True).start()
    return jsonify({"message": "Export started. You will be notified when it is ready.", "job": job.to_dict()}), 202


@bp.get("/exports")
@auth_required("user")
def list_exports():
    jobs = ExportJob.query.filter_by(user_id=g.user.id).order_by(ExportJob.id.desc()).limit(10).all()
    return jsonify([j.to_dict() for j in jobs])


@bp.get("/exports/<int:job_id>/download")
@auth_required("user")
def download_export(job_id):
    job = ExportJob.query.filter_by(id=job_id, user_id=g.user.id).first()
    if not job or job.status != "Done":
        return err("Export is not ready", 404)
    return send_file(job.file_path, mimetype="text/csv", as_attachment=True,
                     download_name="trekking_history.csv")


@bp.get("/notifications")
@auth_required()
def notifications():
    rows = Notification.query.filter_by(user_id=g.user.id).order_by(Notification.id.desc()).limit(30).all()
    return jsonify({"items": [n.to_dict() for n in rows],
                    "unread": Notification.query.filter_by(user_id=g.user.id, is_read=False).count()})


@bp.post("/notifications/read")
@auth_required()
def mark_read():
    Notification.query.filter_by(user_id=g.user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"message": "ok"})
