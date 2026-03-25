"""
prediction.py – ML prediction blueprint.
Loads saved model artifacts and exposes POST /prediction/predict.

Integrates with recommendation.py for education-weighted re-ranking:
1. ML model produces top-N predicted roles with probabilities.
2. recommend_jobs() re-ranks using weighted composite score
   (education 40%, skills 30%, resume 20%, certifications 10%).
3. If branch/specialization are missing, gracefully falls back to
   ML-only predictions for full backward compatibility.
"""

import os
import logging

import joblib
import pandas as pd
import numpy as np
from flask import Blueprint, request, jsonify

from auth import token_required
from recommendation import recommend_jobs

logger = logging.getLogger(__name__)

prediction_bp = Blueprint("prediction", __name__, url_prefix="/prediction")

# ---------------------------------------------------------------------------
# Paths to saved model artifacts
# ---------------------------------------------------------------------------
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ml_model")

_artifacts = {}


def load_model():
    """Load model artifacts at startup. Safe if files are missing."""
    files = {
        "model": "model.pkl",
        "scaler": "scaler.pkl",
        "encoder_degree": "encoder_degree.pkl",
        "encoder_branch": "encoder_branch.pkl",
        "encoder_role": "encoder_role.pkl",
        "feature_columns": "feature_columns.pkl",
    }
    for key, fname in files.items():
        path = os.path.join(MODEL_DIR, fname)
        if os.path.exists(path):
            _artifacts[key] = joblib.load(path)
            logger.info(f"Loaded {fname}")
        else:
            logger.warning(f"Model artifact missing: {fname}")

    if "model" in _artifacts:
        logger.info("ML model ready for predictions.")
    else:
        logger.warning("ML model NOT available – predictions will return errors.")


# ---------------------------------------------------------------------------
# POST /prediction/predict
# ---------------------------------------------------------------------------

@prediction_bp.route("/predict", methods=["POST"])
@token_required
def predict():
    # Check model availability
    if "model" not in _artifacts:
        return jsonify({
            "error": "ML model is not available. Please run train_model.py first."
        }), 503

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    required = ["degree", "gpa", "experience", "certifications"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        model = _artifacts["model"]
        scaler = _artifacts["scaler"]
        le_degree = _artifacts["encoder_degree"]
        le_role = _artifacts["encoder_role"]
        feature_columns = _artifacts["feature_columns"]

        # Optional: branch encoder (backward compatible if not present)
        le_branch = _artifacts.get("encoder_branch")

        # ------ parse input fields ------
        skills_input = data.get("skills", "")
        if not skills_input:
            skills_list = []
        elif isinstance(skills_input, str):
            skills_list = [s.strip().lower().replace(" ", "_") for s in skills_input.split(",") if s.strip()]
        else:
            skills_list = [s.strip().lower().replace(" ", "_") for s in skills_input if str(s).strip()]

        degree_val = data["degree"]
        if degree_val in le_degree.classes_:
            degree_encoded = le_degree.transform([degree_val])[0]
        else:
            degree_encoded = 0

        # Branch (optional field – backward compatible)
        branch_val = data.get("branch", "")
        branch_encoded = 0
        if le_branch and branch_val:
            if branch_val in le_branch.classes_:
                branch_encoded = le_branch.transform([branch_val])[0]

        # Specialization (optional)
        specialization_val = data.get("specialization", "")

        # ------ build feature vector ------
        row = {
            "degree_encoded": degree_encoded,
            "gpa": float(data["gpa"]),
            "num_certs": int(data.get("certifications_count",
                             len(data["certifications"].split(",")) if isinstance(data["certifications"], str) and data["certifications"] else 0)),
            "num_projects": int(data.get("projects", 2)),
            "num_internships": int(data.get("experience", 0)),
        }

        # Add branch_encoded if it's in the feature columns
        if "branch_encoded" in feature_columns:
            row["branch_encoded"] = branch_encoded

        # Binary skill columns
        all_skill_cols = [c for c in feature_columns if c not in
                         ["degree_encoded", "branch_encoded", "gpa", "num_certs",
                          "num_projects", "num_internships"]]
        for skill_col in all_skill_cols:
            row[skill_col] = 1 if skill_col in skills_list else 0

        df_input = pd.DataFrame([row])
        for col in feature_columns:
            if col not in df_input.columns:
                df_input[col] = 0
        df_input = df_input[feature_columns]

        X_scaled = scaler.transform(df_input)

        # ------ ML predict: get top 5 roles ------
        probs = model.predict_proba(X_scaled)[0]
        top_n = min(5, len(probs))
        top_idx = probs.argsort()[-top_n:][::-1]
        top_roles = le_role.inverse_transform(top_idx)
        top_probs = probs[top_idx]

        ml_predictions = []
        for role, prob in zip(top_roles, top_probs):
            ml_predictions.append({
                "role": role,
                "confidence": round(float(prob) * 100, 2),
            })

        # ------ Re-rank with weighted scoring engine ------
        # Parse user skills back to readable format for recommendation engine
        readable_skills = data.get("skills", "")
        if not readable_skills:
            readable_skills = []
        elif isinstance(readable_skills, str):
            readable_skills = [s.strip() for s in readable_skills.split(",") if s.strip()]

        recommendations = recommend_jobs(
            ml_predictions=ml_predictions,
            user_degree=degree_val,
            user_branch=branch_val,
            user_specialization=specialization_val,
            user_skills=readable_skills,
            user_certs=data.get("certifications", ""),
            gpa=float(data["gpa"]),
            experience=int(data.get("experience", 0)),
            num_projects=int(data.get("projects", 2)),
        )

        # ------ Build response ------
        # Use the re-ranked results as primary predictions
        predictions = []
        for rec in recommendations[:3]:
            predictions.append({
                "role": rec["role"],
                "confidence": rec["final_score"],
                "ml_confidence": rec["ml_confidence"],
                "education_score": rec["education_score"],
                "skills_score": rec["skills_score"],
                "resume_score": rec["resume_score"],
                "certifications_score": rec["certifications_score"],
                "explanations": rec["explanations"],
            })

        # ------ explanation for backward compatibility ------
        explanation = _generate_explanation(df_input, feature_columns, X_scaled, predictions[0]["role"] if predictions else "")

        return jsonify({
            "predictions": predictions,
            "explanation": explanation,
        }), 200

    except Exception as e:
        logger.exception("Prediction failed")
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


def _generate_explanation(df_input, feature_columns, X_scaled, top_role):
    """Generate a human-readable explanation of which features mattered."""
    try:
        model = _artifacts["model"]
        importances = None

        # Try feature importances (tree models) or coefficients (linear models)
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        elif hasattr(model, "coef_"):
            importances = np.abs(model.coef_).mean(axis=0)

        if importances is None:
            return ["Prediction based on your overall profile."]

        paired = list(zip(feature_columns, importances))
        paired.sort(key=lambda x: x[1], reverse=True)

        explanations = []
        for feat, imp in paired[:3]:
            val = df_input[feat].iloc[0]
            if val > 0:
                nice = feat.replace("_", " ").title()
                explanations.append(
                    f"Your '{nice}' strongly contributed to predicting '{top_role}'."
                )
            else:
                nice = feat.replace("_", " ").title()
                explanations.append(
                    f"Improving '{nice}' could strengthen your profile."
                )
        return explanations

    except Exception:
        return ["Prediction based on your overall profile."]




#----------------new updated code--------------------------------#
# """
# prediction.py – ML prediction blueprint.
# Loads saved model artifacts and exposes POST /prediction/predict.

# Integrates with recommendation.py for education-weighted re-ranking:
# 1. ML model produces top-N predicted roles with probabilities.
# 2. recommend_jobs() re-ranks using weighted composite score
#    (education 40%, skills 30%, resume 20%, certifications 10%).
# 3. If branch/specialization are missing, gracefully falls back to
#    ML-only predictions for full backward compatibility.
# """

# import os
# import logging

# import joblib
# import pandas as pd
# import numpy as np
# from flask import Blueprint, request, jsonify

# from auth import token_required
# from recommendation import recommend_jobs

# logger = logging.getLogger(__name__)

# prediction_bp = Blueprint("prediction", __name__, url_prefix="/prediction")

# # ---------------------------------------------------------------------------
# # Paths to saved model artifacts
# # ---------------------------------------------------------------------------
# MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ml_model")

# _artifacts = {}


# def load_model():
#     """Load model artifacts at startup. Safe if files are missing."""
#     files = {
#         "model": "model.pkl",
#         "scaler": "scaler.pkl",
#         "encoder_degree": "encoder_degree.pkl",
#         "encoder_branch": "encoder_branch.pkl",
#         "encoder_role": "encoder_role.pkl",
#         "feature_columns": "feature_columns.pkl",
#     }
#     for key, fname in files.items():
#         path = os.path.join(MODEL_DIR, fname)
#         if os.path.exists(path):
#             _artifacts[key] = joblib.load(path)
#             logger.info(f"Loaded {fname}")
#         else:
#             logger.warning(f"Model artifact missing: {fname}")

#     if "model" in _artifacts:
#         logger.info("ML model ready for predictions.")
#     else:
#         logger.warning("ML model NOT available – predictions will return errors.")


# # ---------------------------------------------------------------------------
# # POST /prediction/predict
# # ---------------------------------------------------------------------------

# @prediction_bp.route("/predict", methods=["POST"])
# @token_required
# def predict():
#     # Check model availability
#     if "model" not in _artifacts:
#         return jsonify({
#             "error": "ML model is not available. Please run train_model.py first."
#         }), 503

#     try:
#         data = request.get_json(force=True)
#     except Exception:
#         return jsonify({"error": "Invalid JSON body"}), 400

#     required = ["degree", "skills", "gpa", "experience", "certifications"]
#     missing = [f for f in required if f not in data]
#     if missing:
#         return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

#     try:
#         model = _artifacts["model"]
#         scaler = _artifacts["scaler"]
#         le_degree = _artifacts["encoder_degree"]
#         le_role = _artifacts["encoder_role"]
#         feature_columns = _artifacts["feature_columns"]

#         # Optional: branch encoder (backward compatible if not present)
#         le_branch = _artifacts.get("encoder_branch")

#         # ------ parse input fields ------
#         skills_input = data["skills"]
#         if isinstance(skills_input, str):
#             skills_list = [s.strip().lower().replace(" ", "_") for s in skills_input.split(",")]
#         else:
#             skills_list = [s.strip().lower().replace(" ", "_") for s in skills_input]

#         degree_val = data["degree"]
#         if degree_val in le_degree.classes_:
#             degree_encoded = le_degree.transform([degree_val])[0]
#         else:
#             degree_encoded = 0

#         # Branch (optional field – backward compatible)
#         branch_val = data.get("branch", "")
#         branch_encoded = 0
#         if le_branch and branch_val:
#             if branch_val in le_branch.classes_:
#                 branch_encoded = le_branch.transform([branch_val])[0]

#         # Specialization (optional)
#         specialization_val = data.get("specialization", "")

#         # ------ build feature vector ------
#         # Fixed logic for num_certs to handle strings and integers correctly
#         raw_certs = data.get("certifications", "")
#         if isinstance(raw_certs, str) and raw_certs.strip():
#             num_certs = len(raw_certs.split(","))
#         elif isinstance(raw_certs, list):
#             num_certs = len(raw_certs)
#         else:
#             num_certs = 0

#         row = {
#             "degree_encoded": degree_encoded,
#             "gpa": float(data["gpa"]),
#             "num_certs": num_certs,
#             "num_projects": int(data.get("projects", 2)),
#             "num_internships": int(data.get("experience", 0)),
#         }

#         # Add branch_encoded if it's in the feature columns
#         if "branch_encoded" in feature_columns:
#             row["branch_encoded"] = branch_encoded

#         # Binary skill columns
#         all_skill_cols = [c for c in feature_columns if c not in
#                          ["degree_encoded", "branch_encoded", "gpa", "num_certs",
#                           "num_projects", "num_internships"]]
#         for skill_col in all_skill_cols:
#             row[skill_col] = 1 if skill_col in skills_list else 0

#         df_input = pd.DataFrame([row])
#         for col in feature_columns:
#             if col not in df_input.columns:
#                 df_input[col] = 0
#         df_input = df_input[feature_columns]

#         X_scaled = scaler.transform(df_input)

#         # ------ ML predict: get top 5 roles ------
#         probs = model.predict_proba(X_scaled)[0]
#         top_n = min(5, len(probs))
#         top_idx = probs.argsort()[-top_n:][::-1]
#         top_roles = le_role.inverse_transform(top_idx)
#         top_probs = probs[top_idx]

#         ml_predictions = []
#         for role, prob in zip(top_roles, top_probs):
#             ml_predictions.append({
#                 "role": role,
#                 "confidence": round(float(prob) * 100, 2),
#             })

#         # ------ Re-rank with weighted scoring engine ------
#         readable_skills = data["skills"]
#         if isinstance(readable_skills, str):
#             readable_skills = [s.strip() for s in readable_skills.split(",") if s.strip()]

#         recommendations = recommend_jobs(
#             ml_predictions=ml_predictions,
#             user_degree=degree_val,
#             user_branch=branch_val,
#             user_specialization=specialization_val,
#             user_skills=readable_skills,
#             user_certs=data.get("certifications", ""),
#             gpa=float(data["gpa"]),
#             experience=int(data.get("experience", 0)),
#             num_projects=int(data.get("projects", 2)),
#         )

#         # ------ Build response ------
#         predictions = []
#         for rec in recommendations[:3]:
#             predictions.append({
#                 "role": rec["role"],
#                 "confidence": rec["final_score"],
#                 "ml_confidence": rec["ml_confidence"],
#                 "education_score": rec["education_score"],
#                 "skills_score": rec["skills_score"],
#                 "resume_score": rec["resume_score"],
#                 "certifications_score": rec["certifications_score"],
#                 "explanations": rec["explanations"],
#             })

#         # ------ explanation for backward compatibility ------
#         explanation = _generate_explanation(df_input, feature_columns, X_scaled, predictions[0]["role"] if predictions else "")

#         return jsonify({
#             "predictions": predictions,
#             "explanation": explanation,
#         }), 200

#     except Exception as e:
#         logger.exception("Prediction failed")
#         return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


# def _generate_explanation(df_input, feature_columns, X_scaled, top_role):
#     """Generate a human-readable explanation of which features mattered."""
#     try:
#         model = _artifacts["model"]
#         importances = None

#         if hasattr(model, "feature_importances_"):
#             importances = model.feature_importances_
#         elif hasattr(model, "coef_"):
#             importances = np.abs(model.coef_).mean(axis=0)

#         if importances is None:
#             return ["Prediction based on your overall profile."]

#         paired = list(zip(feature_columns, importances))
#         paired.sort(key=lambda x: x[1], reverse=True)

#         explanations = []
#         for feat, imp in paired[:3]:
#             val = df_input[feat].iloc[0]
#             nice = feat.replace("_", " ").title()
            
#             # Updated Logic: Only suggest improvement if value is zero or low
#             if val > 0:
#                 explanations.append(
#                     f"Your '{nice}' level is a strong foundation for your predicted role."
#                 )
#             else:
#                 explanations.append(
#                     f"Adding more to your '{nice}' could further strengthen your profile."
#                 )
#         return explanations

#     except Exception:
#         return ["Prediction based on your overall profile."]