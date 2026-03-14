"""
auth.py – Authentication blueprint (signup, login) with JWT.
Uses bcrypt for reliable password hashing across all platforms.
"""

import os
import datetime
import functools
import logging

from flask import Blueprint, request, jsonify, g
import jwt
import bcrypt

from database import find_user_by_email, insert_user

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

SECRET_KEY = os.getenv("JWT_SECRET", "edu2job-super-secret-key-change-me")
TOKEN_EXPIRY_HOURS = 24


# ---------------------------------------------------------------------------
# Password hashing utilities (bcrypt)
# ---------------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """Hash a plain-text password and return the hash as a UTF-8 string."""
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")          # store as string in MongoDB


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Compare a plain-text password against a stored bcrypt hash."""
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode("utf-8")   # bcrypt needs bytes
    return bcrypt.checkpw(plain_password.encode("utf-8"), stored_hash)


# ---------------------------------------------------------------------------
# JWT helper – decorator for protected routes
# ---------------------------------------------------------------------------

def token_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            g.current_user_email = payload["email"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# POST /auth/signup
# ---------------------------------------------------------------------------

@auth_bp.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    required = ["full_name", "email", "password"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    email = data["email"].strip().lower()

    if find_user_by_email(email):
        return jsonify({"error": "Email already registered"}), 409

    hashed_pw = hash_password(data["password"])
    logger.info(f"[SIGNUP] Hashing password for {email} (hash starts with: {hashed_pw[:10]}...)")

    user_doc = {
        "full_name": data["full_name"],
        "email": email,
        "password_hash": hashed_pw,
        "degree": data.get("degree", ""),
        "skills": data.get("skills", ""),
        "gpa": float(data.get("gpa", 0)),
        "experience": int(data.get("experience", 0)),
        "certifications": data.get("certifications", ""),
    }

    user_id = insert_user(user_doc)
    logger.info(f"[SIGNUP] User registered successfully: {email} (id={user_id})")
    return jsonify({"message": "Registration successful", "user_id": user_id}), 201


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = find_user_by_email(email)

    # --- Debug: user lookup ---
    if not user:
        logger.warning(f"[LOGIN] User not found for email: {email}")
        return jsonify({"error": "Invalid email or password"}), 401

    logger.info(f"[LOGIN] User found: email={user['email']}, name={user.get('full_name')}")

    # --- Debug: password verification ---
    stored_hash = user.get("password_hash", "")
    if not stored_hash:
        logger.error(f"[LOGIN] No password_hash field for user: {email}")
        return jsonify({"error": "Invalid email or password"}), 401

    password_ok = verify_password(password, stored_hash)
    logger.info(f"[LOGIN] Password check result: {password_ok}")

    if not password_ok:
        return jsonify({"error": "Invalid email or password"}), 401

    payload = {
        "email": user["email"],
        "full_name": user["full_name"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRY_HOURS),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    logger.info(f"[LOGIN] Login successful for: {email}")
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "full_name": user["full_name"],
            "email": user["email"],
            "degree": user.get("degree", ""),
            "skills": user.get("skills", ""),
            "gpa": user.get("gpa", 0),
            "experience": user.get("experience", 0),
            "certifications": user.get("certifications", ""),
        },
    }), 200
