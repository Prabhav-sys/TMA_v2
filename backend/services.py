import csv
import json
import os
import smtplib
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy import func

from config import Config
from extensions import db
from models import Booking, ExportJob, Trek, User, notify


def send_email(to, subject, html):
    if Config.SMTP_HOST:
        msg = MIMEMultipart("alternative")
        msg["Subject"], msg["From"], msg["To"] = subject, Config.MAIL_FROM, to
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=20) as s:
            s.starttls()
            if Config.SMTP_USER:
                s.login(Config.SMTP_USER, Config.SMTP_PASS)
            s.sendmail(Config.MAIL_FROM, [to], msg.as_string())
        return "smtp"
    os.makedirs(Config.OUTBOX_DIR, exist_ok=True)
    safe = "".join(c if c.isalnum() else "_" for c in f"{to}_{subject}")[:80]
    path = os.path.join(Config.OUTBOX_DIR, f"{datetime.now():%Y%m%d_%H%M%S}_{safe}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"<!-- To: {to} | Subject: {subject} -->\n{html}")
    return "outbox"


def send_gchat(text):
    if not Config.GCHAT_WEBHOOK_URL:
        return False
    req = urllib.request.Request(
        Config.GCHAT_WEBHOOK_URL, data=json.dumps({"text": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=15)
    return True


def send_daily_reminders():
    today = date.today()
    limit = today + timedelta(days=Config.REMINDER_DAYS_AHEAD)
    bookings = (Booking.query.join(Trek).filter(
        Booking.status == "Booked", Trek.start_date >= today, Trek.start_date <= limit,
        Trek.status.in_(["Approved", "Open", "Closed"])).all())
    sent = 0
    for b in bookings:
        t, u = b.trek, b.user
        if u.status != "active":
            continue
        days = (t.start_date - today).days
        when = "today" if days == 0 else f"in {days} day(s)"
        text = (f"Hi {u.name}, your trek '{t.name}' ({t.location}) starts on "
                f"{t.start_date:%d %b %Y} ({when}). Instructions: {t.instructions or 'Carry ID proof and water.'}")
        notify(u.id, f"Reminder: {t.name} starts {when} ({t.start_date:%d %b}).", "warning")
        html = f"<h2>Trek reminder</h2><p>{text}</p>"
        try:
            send_email(u.email, f"Reminder: {t.name} starts {when}", html)
            send_gchat(text)
        except Exception as exc:
            print("reminder delivery failed:", exc)
        sent += 1
    db.session.commit()
    return sent


def month_range(year, month):
    start = date(year, month, 1)
    end = date(year + (month == 12), month % 12 + 1, 1)
    return start, end


def report_data(year, month):
    start, end = month_range(year, month)
    conducted = Trek.query.filter(Trek.status.in_(["Ongoing", "Completed"]),
                                  Trek.start_date >= start, Trek.start_date < end).all()
    ids = [t.id for t in conducted]
    participants = 0
    if ids:
        participants = (db.session.query(func.count(func.distinct(Booking.user_id)))
                        .filter(Booking.trek_id.in_(ids), Booking.status != "Cancelled").scalar())
    made = Booking.query.filter(Booking.booking_date >= datetime.combine(start, datetime.min.time()),
                                Booking.booking_date < datetime.combine(end, datetime.min.time()))
    counts = Counter(b.trek.name for b in made.filter(Booking.status != "Cancelled").all())
    return {
        "month": f"{start:%B %Y}", "year": year, "month_no": month,
        "treks_conducted": len(conducted),
        "users_participated": participants,
        "new_bookings": made.filter(Booking.status != "Cancelled").count(),
        "cancellations": made.filter(Booking.status == "Cancelled").count(),
        "new_users": User.query.filter(User.role == "user", User.created_at >= start, User.created_at < end).count(),
        "popular_treks": [{"name": n, "bookings": c} for n, c in counts.most_common(5)],
        "conducted_list": [{"name": t.name, "location": t.location, "start_date": t.start_date.isoformat(),
                            "participants": t.total_slots - t.available_slots} for t in conducted],
    }


def render_report_html(d):
    pop = "".join(
        f"<tr><td>{p['name']}</td><td style='text-align:right'>{p['bookings']}</td></tr>"
        for p in d["popular_treks"]
    ) or "<tr><td colspan='2'>No bookings this month</td></tr>"

    conducted = "".join(
        f"<tr><td>{c['name']}</td><td>{c['location']}</td><td>{c['start_date']}</td>"
        f"<td style='text-align:right'>{c['participants']}</td></tr>"
        for c in d["conducted_list"]
    ) or "<tr><td colspan='4'>None</td></tr>"

    box = "display:inline-block;margin:6px;padding:14px 22px;background:#f1f5ee;border-radius:10px;text-align:center"

    return f"""
    <div style="font-family:Arial,sans-serif;max-width:640px;margin:auto;color:#1f2a24">
      <h1 style="color:#2f5d46">Monthly Trekking Report - {d['month']}</h1>
      <div>
        <span style="{box}"><b style="font-size:26px">{d['treks_conducted']}</b><br>Treks conducted</span>
        <span style="{box}"><b style="font-size:26px">{d['users_participated']}</b><br>Users participated</span>
        <span style="{box}"><b style="font-size:26px">{d['new_bookings']}</b><br>New bookings</span>
        <span style="{box}"><b style="font-size:26px">{d['cancellations']}</b><br>Cancellations</span>
      </div>
      <h3>Popular treks</h3>
      <table width="100%" cellpadding="6" border="1" style="border-collapse:collapse">
        <tr style="background:#2f5d46;color:#fff">
          <th align="left">Trek</th>
          <th align="right">Bookings</th>
        </tr>
        {pop}
      </table>
      <h3>Treks conducted</h3>
      <table width="100%" cellpadding="6" border="1" style="border-collapse:collapse">
        <tr style="background:#2f5d46;color:#fff">
          <th align="left">Trek</th>
          <th align="left">Location</th>
          <th align="left">Start</th>
          <th align="right">Trekkers</th>
        </tr>
        {conducted}
      </table>
    </div>
    """



def send_monthly_report(year=None, month=None):
    if not year or not month:
        first = date.today().replace(day=1)
        prev = first - timedelta(days=1)
        year, month = prev.year, prev.month
    data = report_data(year, month)
    html = render_report_html(data)
    for admin in User.query.filter_by(role="admin").all():
        send_email(admin.email, f"Monthly Trekking Report - {data['month']}", html)
        notify(admin.id, f"Monthly report for {data['month']} has been generated and mailed.", "success")
    db.session.commit()
    return data["month"]


def export_booking_history(job_id):
    job = db.session.get(ExportJob, job_id)
    try:
        rows = (Booking.query.filter_by(user_id=job.user_id).join(Trek)
                .order_by(Trek.start_date.desc()).all())
        os.makedirs(Config.EXPORT_DIR, exist_ok=True)
        path = os.path.join(Config.EXPORT_DIR, f"bookings_user{job.user_id}_{job.id}.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["User ID", "Booking ID", "Trek Name", "Location", "Difficulty", "Booking Status",
                        "Booking Date", "Trek Start Date", "Trek End Date"])
            for b in rows:
                w.writerow([b.user_id, b.id, b.trek.name, b.trek.location, b.trek.difficulty, b.status,
                            b.booking_date.strftime("%Y-%m-%d"),
                            b.trek.start_date, b.trek.end_date])
        job.status, job.file_path = "Done", path
        notify(job.user_id, "Your trekking history CSV is ready to download.", "success")
    except Exception as exc:
        job.status = "Failed"
        notify(job.user_id, f"Export failed: {exc}", "warning")
    db.session.commit()
