from datetime import datetime, date

from sqlalchemy import Index, text
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default="user")
    contact = db.Column(db.String(20))
    status = db.Column(db.String(12), nullable=False, default="active")
    experience_years = db.Column(db.Integer)
    specialization = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    def to_dict(self):
        data = {
            "id": self.id, "name": self.name, "email": self.email, "role": self.role,
            "contact": self.contact, "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else None,
        }
        if self.role == "staff":
            data["experience_years"] = self.experience_years
            data["specialization"] = self.specialization
            data["assigned_treks"] = [t.name for t in self.assigned_treks]
        return data


class Trek(db.Model):
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    difficulty = db.Column(db.String(10), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    total_slots = db.Column(db.Integer, nullable=False, default=10)
    available_slots = db.Column(db.Integer, nullable=False, default=10)
    staff_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    status = db.Column(db.String(12), nullable=False, default="Pending")
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    altitude_m = db.Column(db.Integer)
    description = db.Column(db.Text)
    instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    staff = db.relationship("User", backref="assigned_treks", foreign_keys=[staff_id])

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "location": self.location,
            "difficulty": self.difficulty, "duration_days": self.duration_days,
            "total_slots": self.total_slots, "available_slots": self.available_slots,
            "registered": self.total_slots - self.available_slots,
            "staff_id": self.staff_id, "staff_name": self.staff.name if self.staff else None,
            "status": self.status,
            "start_date": self.start_date.isoformat(), "end_date": self.end_date.isoformat(),
            "altitude_m": self.altitude_m,
            "description": self.description, "instructions": self.instructions,
        }


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(12), nullable=False, default="Booked")
    cancelled_at = db.Column(db.DateTime)

    user = db.relationship("User", backref="bookings")
    trek = db.relationship("Trek", backref="bookings")

    __table_args__ = (
        Index("uq_active_booking", "user_id", "trek_id", unique=True,
              sqlite_where=text("status = 'Booked'")),
    )

    def to_dict(self):
        t = self.trek
        return {
            "id": self.id, "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "user_email": self.user.email if self.user else None,
            "user_contact": self.user.contact if self.user else None,
            "trek_id": self.trek_id, "trek_name": t.name, "location": t.location,
            "difficulty": t.difficulty, "trek_status": t.status,
            "start_date": t.start_date.isoformat(), "end_date": t.end_date.isoformat(),
            "booking_date": self.booking_date.strftime("%Y-%m-%d %H:%M"),
            "status": self.status,
            "completed_on": t.end_date.isoformat() if self.status == "Completed" else None,
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message = db.Column(db.String(300), nullable=False)
    kind = db.Column(db.String(20), default="info")
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "message": self.message, "kind": self.kind,
                "is_read": self.is_read, "created_at": self.created_at.strftime("%d %b %H:%M")}


class ExportJob(db.Model):
    __tablename__ = "export_jobs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(10), default="Pending")
    file_path = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "status": self.status,
                "created_at": self.created_at.strftime("%d %b %Y %H:%M")}


def notify(user_id, message, kind="info"):
    db.session.add(Notification(user_id=user_id, message=message, kind=kind))
