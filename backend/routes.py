"""
routes.py – Register all API blueprints and add profile / resume routes.
"""

import os
import logging

from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename

from auth import token_required
from database import find_user_by_email, update_user, add_prediction, get_predictions

logger = logging.getLogger(__name__)

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")
resume_bp = Blueprint("resume", __name__, url_prefix="/resume")

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------------------------------------------------------------------
# POST /profile/update
# ---------------------------------------------------------------------------

@profile_bp.route("/update", methods=["POST"])
@token_required
def update_profile():
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    allowed_fields = ["full_name", "degree", "branch", "specialization", "skills", "gpa", "experience", "certifications"]
    update_data = {k: data[k] for k in allowed_fields if k in data}

    if not update_data:
        return jsonify({"error": "No valid fields to update"}), 400

    # Coerce types
    if "gpa" in update_data:
        update_data["gpa"] = float(update_data["gpa"])
    if "experience" in update_data:
        update_data["experience"] = int(update_data["experience"])

    success = update_user(g.current_user_email, update_data)
    if success:
        return jsonify({"message": "Profile updated successfully"}), 200
    else:
        return jsonify({"error": "User not found"}), 404


@profile_bp.route("/me", methods=["GET"])
@token_required
def get_profile():
    user = find_user_by_email(g.current_user_email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.pop("password_hash", None)
    return jsonify({"user": user}), 200


@profile_bp.route("/predictions", methods=["GET"])
@token_required
def fetch_predictions():
    """Return all saved predictions for the logged-in user."""
    preds = get_predictions(g.current_user_email)
    return jsonify({"predictions": preds}), 200


@profile_bp.route("/predictions", methods=["POST"])
@token_required
def save_prediction():
    """Save a new prediction to the user's history."""
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    prediction = {
        "role": data.get("role", ""),
        "confidence": data.get("confidence", 0),
        "date": data.get("date", ""),
    }
    add_prediction(g.current_user_email, prediction)
    return jsonify({"message": "Prediction saved"}), 201


# ---------------------------------------------------------------------------
# POST /resume/upload
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt"}


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@resume_bp.route("/upload", methods=["POST"])
@token_required
def upload_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not _allowed_file(file.filename):
        return jsonify({"error": f"Allowed file types: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, f"{g.current_user_email}_{filename}")
    file.save(save_path)

    # Update user record with resume path
    update_user(g.current_user_email, {"resume_path": save_path})

    # Parse resume and extract profile data
    from resume_parser import parse_resume
    parsed = parse_resume(save_path)

    # Auto-update user profile with extracted data (only non-empty fields)
    auto_fields = {}
    if parsed.get("degree"):
        auto_fields["degree"] = parsed["degree"]
    if parsed.get("branch"):
        auto_fields["branch"] = parsed["branch"]
    if parsed.get("skills"):
        auto_fields["skills"] = ", ".join(parsed["skills"])
    if parsed.get("gpa") and parsed["gpa"] > 0:
        auto_fields["gpa"] = parsed["gpa"]
    if parsed.get("experience") and parsed["experience"] > 0:
        auto_fields["experience"] = parsed["experience"]
    if parsed.get("certifications"):
        auto_fields["certifications"] = parsed["certifications"]
    if auto_fields:
        update_user(g.current_user_email, auto_fields)

    logger.info(f"Resume uploaded and parsed for {g.current_user_email}: {save_path}")
    return jsonify({
        "message": "Resume uploaded and parsed successfully",
        "filename": filename,
        "parsed": parsed,
    }), 200


# ---------------------------------------------------------------------------
# Helper – register all blueprints on the app
# ---------------------------------------------------------------------------

def register_routes(app):
    from auth import auth_bp
    from prediction import prediction_bp
    from charts import charts_bp
    from quiz import quiz_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(charts_bp)
    app.register_blueprint(quiz_bp)

    logger.info("All routes registered.")
