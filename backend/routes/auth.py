from flask import Blueprint, g, jsonify, request

from extensions import db
from models import User
from .utils import auth_required, err, make_token, valid_contact, valid_email

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
def register():
    """Only trekkers can self-register. Staff are created by admin, admin by code."""
    d = request.get_json(silent=True) or {}
    name, email = (d.get("name") or "").strip(), (d.get("email") or "").strip().lower()
    password, contact = d.get("password") or "", (d.get("contact") or "").strip()
    if len(name) < 2:
        return err("Name must be at least 2 characters")
    if not valid_email(email):
        return err("Enter a valid email address")
    if len(password) < 6:
        return err("Password must be at least 6 characters")
    if contact and not valid_contact(contact):
        return err("Enter a valid contact number")
    if User.query.filter_by(email=email).first():
        return err("An account with this email already exists", 409)
    user = User(name=name, email=email, contact=contact, role="user")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Registration successful. Please log in."}), 201


@bp.post("/login")
def login():
    d = request.get_json(silent=True) or {}
    email, password = (d.get("email") or "").strip().lower(), d.get("password") or ""
    wanted_role = d.get("role")
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return err("Invalid email or password", 401)
    if wanted_role and wanted_role != user.role:
        return err(f"No {wanted_role} account found with these credentials", 401)
    if user.status != "active":
        return err(f"Your account is {user.status}. Contact the admin.", 403)
    return jsonify({"token": make_token(user), "user": user.to_dict()})


@bp.get("/me")
@auth_required()
def me():
    return jsonify(g.user.to_dict())


@bp.put("/me")
@auth_required()
def update_me():
    d, u = request.get_json(silent=True) or {}, g.user
    if "name" in d:
        if len((d["name"] or "").strip()) < 2:
            return err("Name must be at least 2 characters")
        u.name = d["name"].strip()
    if "contact" in d:
        if d["contact"] and not valid_contact(d["contact"]):
            return err("Enter a valid contact number")
        u.contact = (d["contact"] or "").strip()
    if d.get("new_password"):
        if not u.check_password(d.get("current_password") or ""):
            return err("Current password is incorrect")
        if len(d["new_password"]) < 6:
            return err("New password must be at least 6 characters")
        u.set_password(d["new_password"])
    db.session.commit()
    return jsonify({"message": "Profile updated", "user": u.to_dict()})
