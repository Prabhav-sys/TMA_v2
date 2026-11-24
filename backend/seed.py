from datetime import date, timedelta

from app import get_flask_app
from extensions import db
from models import Trek, User


def person(name, email, role, contact, **extra):
    if User.query.filter_by(email=email).first():
        return User.query.filter_by(email=email).first()
    u = User(name=name, email=email, role=role, contact=contact, status="active", **extra)
    u.set_password("pass123")
    db.session.add(u)
    db.session.commit()
    return u


with get_flask_app().app_context():
    s1 = person("Vikram Singh", "vikram@trek.com", "staff", "9876543210", experience_years=8, specialization="High Altitude")
    s2 = person("Neha Joshi", "neha@trek.com", "staff", "9123456780", experience_years=5, specialization="First Aid")
    for n, e, c in [
        ("Amit Sharma", "amit@gmail.com", "9812345678"),
        ("Priya Patel", "priya@gmail.com", "9123456789"),
        ("Rahul Verma", "rahul@gmail.com", "9988776655"),
    ]:
        person(n, e, "user", c)

    if Trek.query.count() == 0:
        today = date.today()
        rows = [
            ("Everest Base Camp", "Nepal", "Hard", 12, 20, "Open", 20, 5364, s1),
            ("Roopkund Trek", "Uttarakhand", "Moderate", 7, 15, "Open", 12, 4800, s1),
            ("Kedarkantha Trek", "Uttarakhand", "Easy", 5, 25, "Open", 8, 3800, s2),
            ("Hampta Pass", "Himachal", "Moderate", 5, 12, "Closed", 30, 4270, s2),
            ("Valley of Flowers", "Uttarakhand", "Easy", 6, 18, "Approved", 40, 3658, None),
        ]
        for name, loc, diff, days, slots, status, offset, alt, staff in rows:
            start = today + timedelta(days=offset)
            db.session.add(
                Trek(
                    name=name,
                    location=loc,
                    difficulty=diff,
                    duration_days=days,
                    total_slots=slots,
                    available_slots=slots,
                    status=status,
                    start_date=start,
                    end_date=start + timedelta(days=days - 1),
                    altitude_m=alt,
                    staff_id=staff.id if staff else None,
                    description=f"{name} is a {diff.lower()} trek in {loc}, spread over {days} days.",
                    instructions="Report at the base camp at 7 AM. Carry ID proof, warm layers, trekking shoes and 2L of water.",
                )
            )
        db.session.commit()
    print("Seed complete. Logins -> admin@trek.com/admin123, vikram@trek.com/pass123, amit@gmail.com/pass123")
