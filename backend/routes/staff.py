from flask import Blueprint, g, jsonify, request

from cache import cache_clear_treks
from extensions import db
from models import Booking, Trek, notify
from .utils import auth_required, err

bp = Blueprint("staff", __name__, url_prefix="/api/staff")


def _my_trek(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek:
        return None, err("Trek not found", 404)
    if trek.staff_id != g.user.id:
        return None, err("You are not assigned to this trek", 403)
    return trek, None


@bp.get("/dashboard")
@auth_required("staff")
def dashboard():
    treks = Trek.query.filter_by(staff_id=g.user.id).order_by(Trek.start_date).all()
    return jsonify({
        "assigned": len(treks),
        "total_participants": sum(t.total_slots - t.available_slots for t in treks),
        "ongoing": sum(1 for t in treks if t.status == "Ongoing"),
        "treks": [t.to_dict() for t in treks],
    })


@bp.get("/treks/<int:trek_id>")
@auth_required("staff")
def trek_detail(trek_id):
    trek, error = _my_trek(trek_id)
    if error:
        return error
    people = Booking.query.filter_by(trek_id=trek.id).order_by(Booking.booking_date).all()
    return jsonify({"trek": trek.to_dict(), "participants": [b.to_dict() for b in people]})


@bp.put("/treks/<int:trek_id>")
@auth_required("staff")
def update_trek(trek_id):
    trek, error = _my_trek(trek_id)
    if error:
        return error
    d = request.get_json(silent=True) or {}
    if trek.status in ("Ongoing", "Completed"):
        return err(f"A trek that is {trek.status.lower()} can no longer be edited")
    if "total_slots" in d:
        try:
            slots = int(d["total_slots"])
        except (TypeError, ValueError):
            return err("Slots must be a number")
        booked = trek.total_slots - trek.available_slots
        if slots < max(booked, 1):
            return err(f"Slots cannot be lower than the {booked} already booked")
        trek.total_slots, trek.available_slots = slots, slots - booked
    if "status" in d:
        if d["status"] not in ("Open", "Closed"):
            return err("Staff can only set the status to Open or Closed")
        if trek.status == "Pending":
            return err("Wait for the admin to approve this trek first")
        trek.status = d["status"]
    db.session.commit()
    cache_clear_treks()
    return jsonify(trek.to_dict())


@bp.post("/treks/<int:trek_id>/start")
@auth_required("staff")
def start_trek(trek_id):
    trek, error = _my_trek(trek_id)
    if error:
        return error
    if trek.status not in ("Approved", "Open", "Closed"):
        return err(f"A {trek.status} trek cannot be started")
    trek.status = "Ongoing"
    for b in Booking.query.filter_by(trek_id=trek.id, status="Booked"):
        notify(b.user_id, f"Your trek '{trek.name}' has started. Happy trekking!", "info")
    db.session.commit()
    cache_clear_treks()
    return jsonify(trek.to_dict())


@bp.post("/treks/<int:trek_id>/complete")
@auth_required("staff")
def complete_trek(trek_id):
    trek, error = _my_trek(trek_id)
    if error:
        return error
    if trek.status in ("Pending", "Completed"):
        return err(f"A {trek.status} trek cannot be marked completed")
    trek.status = "Completed"
    for b in Booking.query.filter_by(trek_id=trek.id, status="Booked"):
        b.status = "Completed"
        notify(b.user_id, f"'{trek.name}' is complete. It is now in your trekking history.", "success")
    db.session.commit()
    cache_clear_treks()
    return jsonify(trek.to_dict())


@bp.post("/treks/<int:trek_id>/participants/<int:booking_id>/remove")
@auth_required("staff")
def remove_participant(trek_id, booking_id):
    trek, error = _my_trek(trek_id)
    if error:
        return error
    b = Booking.query.filter_by(id=booking_id, trek_id=trek.id, status="Booked").first()
    if not b:
        return err("Active booking not found", 404)
    if trek.status in ("Ongoing", "Completed"):
        return err("Participants cannot be removed once the trek has started")
    b.status = "Cancelled"
    trek.available_slots += 1
    notify(b.user_id, f"Your booking for '{trek.name}' was cancelled by the trek staff.", "warning")
    db.session.commit()
    cache_clear_treks()
    return jsonify({"message": "Participant removed", "trek": trek.to_dict()})
