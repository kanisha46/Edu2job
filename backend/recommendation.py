"""
recommendation.py – Education-prioritized weighted scoring engine.

Provides modular scoring functions and a recommend_jobs() function that
re-ranks ML predictions using a weighted composite score:
    education : 40%   (degree + branch + specialization matching)
    skills    : 30%   (overlap between user skills and role-relevant skills)
    resume    : 20%   (GPA, experience, projects proxy)
    certs     : 10%   (number and relevance of certifications)

Backward compatible: if branch/specialization are missing the engine
falls back to ML-only predictions.
"""

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Weights (must sum to 1.0)
# ---------------------------------------------------------------------------
WEIGHTS = {
    "education": 0.40,
    "skills": 0.30,
    "resume": 0.20,
    "certifications": 0.10,
}

# ---------------------------------------------------------------------------
# Degree hierarchy – maps degree labels to a tier (higher = more advanced)
# ---------------------------------------------------------------------------
DEGREE_TIERS = {
    "PhD": 6,
    "M.Tech": 5, "M.Sc": 5, "MCA": 5, "MBA": 5, "M.E": 5, "M.A": 5,
    "B.Tech": 4, "B.E": 4, "B.Sc": 4, "BCA": 4, "B.A": 4, "B.Com": 4,
    "Diploma": 3,
}

# Related degree equivalences (bidirectional)
DEGREE_EQUIVALENCES = {
    "B.Tech": {"B.E"},
    "B.E": {"B.Tech"},
    "M.Tech": {"M.E"},
    "M.E": {"M.Tech"},
    "B.Sc": {"BCA"},
    "BCA": {"B.Sc"},
    "M.Sc": {"MCA"},
    "MCA": {"M.Sc"},
}

# ---------------------------------------------------------------------------
# Branch similarity mapping
# ---------------------------------------------------------------------------
RELATED_BRANCHES = {
    "Computer Science":       {"IT", "AI/ML", "Data Science", "Software Engineering"},
    "IT":                     {"Computer Science", "AI/ML", "Data Science", "Software Engineering"},
    "AI/ML":                  {"Computer Science", "IT", "Data Science"},
    "Data Science":           {"Computer Science", "IT", "AI/ML"},
    "Software Engineering":   {"Computer Science", "IT"},
    "ECE":                    {"EE", "Electronics"},
    "EE":                     {"ECE", "Electronics"},
    "Electronics":            {"ECE", "EE"},
    "ME":                     {"Automobile", "Production"},
    "Automobile":             {"ME", "Production"},
    "Production":             {"ME", "Automobile"},
    "Civil":                  set(),
    "BBA":                    {"MBA"},
    "MBA":                    {"BBA"},
    "Other":                  set(),
}

# Partial-credit ratio for related (not exact) branch matches
RELATED_BRANCH_CREDIT = 0.6

# ---------------------------------------------------------------------------
# Role → required degree / eligible branches / relevant skills / certs
# This acts as a lightweight "job listing" knowledge base.
# ---------------------------------------------------------------------------
ROLE_PROFILES = {
    "Software Engineer": {
        "required_degrees": ["B.Tech", "B.E", "M.Tech", "MCA", "BCA"],
        "eligible_branches": ["Computer Science", "IT", "Software Engineering"],
        "relevant_skills": ["python", "java", "sql", "javascript", "docker", "git", "linux"],
        "relevant_certs": ["aws certified", "oracle certified", "comptia"],
    },
    "Data Scientist": {
        "required_degrees": ["B.Tech", "M.Tech", "M.Sc", "B.Sc", "PhD"],
        "eligible_branches": ["Computer Science", "Data Science", "AI/ML", "IT"],
        "relevant_skills": ["python", "machine_learning", "sql", "tensorflow", "pytorch",
                            "pandas", "numpy", "data_analysis", "data_science"],
        "relevant_certs": ["data science certification", "machine learning certification",
                           "tensorflow developer", "google cloud certified"],
    },
    "Frontend Developer": {
        "required_degrees": ["B.Tech", "B.E", "BCA", "MCA", "B.Sc"],
        "eligible_branches": ["Computer Science", "IT", "Software Engineering"],
        "relevant_skills": ["javascript", "react", "html", "css", "typescript",
                            "angular", "vue", "next.js", "figma"],
        "relevant_certs": [],
    },
    "Backend Developer": {
        "required_degrees": ["B.Tech", "B.E", "MCA", "M.Tech", "BCA"],
        "eligible_branches": ["Computer Science", "IT", "Software Engineering"],
        "relevant_skills": ["python", "java", "sql", "docker", "node.js",
                            "django", "flask", "spring", "fastapi", "postgresql", "mongodb"],
        "relevant_certs": ["aws certified", "oracle certified"],
    },
    "DevOps Engineer": {
        "required_degrees": ["B.Tech", "B.E", "M.Tech", "MCA"],
        "eligible_branches": ["Computer Science", "IT", "Software Engineering"],
        "relevant_skills": ["aws", "docker", "kubernetes", "terraform", "jenkins",
                            "linux", "python", "bash", "ci/cd"],
        "relevant_certs": ["aws certified", "certified kubernetes", "cka", "ckad",
                           "azure certified", "google cloud certified"],
    },
    "ML Engineer": {
        "required_degrees": ["B.Tech", "M.Tech", "M.Sc", "PhD"],
        "eligible_branches": ["Computer Science", "AI/ML", "Data Science", "IT"],
        "relevant_skills": ["python", "machine_learning", "aws", "tensorflow", "pytorch",
                            "keras", "docker", "scikit-learn"],
        "relevant_certs": ["machine learning certification", "deep learning specialization",
                           "tensorflow developer", "aws certified"],
    },
    "Full Stack Developer": {
        "required_degrees": ["B.Tech", "B.E", "BCA", "MCA", "B.Sc"],
        "eligible_branches": ["Computer Science", "IT", "Software Engineering"],
        "relevant_skills": ["javascript", "react", "python", "sql", "node.js",
                            "html", "css", "docker", "mongodb", "postgresql"],
        "relevant_certs": ["aws certified"],
    },
    "Cloud Architect": {
        "required_degrees": ["B.Tech", "M.Tech", "B.E", "MCA"],
        "eligible_branches": ["Computer Science", "IT", "Software Engineering"],
        "relevant_skills": ["aws", "docker", "python", "kubernetes", "terraform",
                            "azure", "gcp", "linux"],
        "relevant_certs": ["aws certified", "azure certified", "google cloud certified",
                           "certified kubernetes", "cka"],
    },
}

# ---------------------------------------------------------------------------
# Helper: branch similarity check
# ---------------------------------------------------------------------------

def is_related_branch(user_branch: str, eligible_branches: list[str]) -> bool:
    """Return True if user_branch is related to any eligible branch."""
    if not user_branch:
        return False
    ub = user_branch.strip()
    related = RELATED_BRANCHES.get(ub, set())
    return bool(related & set(eligible_branches))


def _normalize(value: float, low: float, high: float) -> float:
    """Clamp and normalize *value* to [0, 1]."""
    if high <= low:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


# ---------------------------------------------------------------------------
# 1. Education score  (degree + branch + specialization)
# ---------------------------------------------------------------------------

def compute_education_score(
    user_degree: str,
    user_branch: str,
    user_specialization: str,
    role_name: str,
) -> tuple[float, list[str]]:
    """
    Return (score ∈ [0,1], explanations[]).

    Breakdown (within the 0-1 range):
        degree match   → 0.50 of total education score
        branch match   → 0.35 of total education score
        specialization → 0.15 bonus
    """
    profile = ROLE_PROFILES.get(role_name)
    if not profile:
        return 0.0, []

    explanations: list[str] = []
    degree_score = 0.0
    branch_score = 0.0
    spec_score = 0.0

    # --- Degree ---
    required = profile["required_degrees"]
    if user_degree in required:
        degree_score = 1.0
        explanations.append(f"Your degree ({user_degree}) matches this role")
    elif user_degree in DEGREE_EQUIVALENCES and DEGREE_EQUIVALENCES[user_degree] & set(required):
        degree_score = 0.85
        explanations.append(f"Your degree ({user_degree}) is equivalent to a required degree")
    else:
        # Give partial credit based on tier closeness
        user_tier = DEGREE_TIERS.get(user_degree, 0)
        max_tier = max((DEGREE_TIERS.get(d, 0) for d in required), default=0)
        if user_tier > 0 and max_tier > 0:
            degree_score = max(0.2, 1.0 - abs(user_tier - max_tier) * 0.2)

    # --- Branch ---
    eligible = profile["eligible_branches"]
    if user_branch:
        ub = user_branch.strip()
        if ub in eligible:
            branch_score = 1.0
            explanations.append(f"Your branch ({ub}) is a direct match")
        elif is_related_branch(ub, eligible):
            branch_score = RELATED_BRANCH_CREDIT
            explanations.append(f"Your branch ({ub}) is related to eligible branches")
        else:
            branch_score = 0.1  # minimal credit for having any branch

    # --- Specialization bonus ---
    if user_specialization:
        spec_lower = user_specialization.strip().lower()
        role_lower = role_name.lower()
        # Check if specialization keywords appear in role name or eligible branches
        if spec_lower in role_lower or any(spec_lower in b.lower() for b in eligible):
            spec_score = 1.0
            explanations.append(f"Your specialization ({user_specialization}) is highly relevant")
        else:
            # Partial credit for having any specialization
            spec_score = 0.3

    # Weighted combination within education sub-score
    total = (degree_score * 0.50) + (branch_score * 0.35) + (spec_score * 0.15)
    return round(total, 4), explanations


# ---------------------------------------------------------------------------
# 2. Skills score
# ---------------------------------------------------------------------------

def compute_skills_score(
    user_skills: list[str],
    role_name: str,
) -> tuple[float, list[str]]:
    """
    Return (score ∈ [0,1], explanations[]).
    Score = |intersection| / |relevant_skills|  (Jaccard-like).
    """
    profile = ROLE_PROFILES.get(role_name)
    if not profile or not profile["relevant_skills"]:
        return 0.0, []

    relevant = set(s.lower().replace(" ", "_") for s in profile["relevant_skills"])
    user_set = set(s.strip().lower().replace(" ", "_") for s in user_skills if s.strip())

    matched = relevant & user_set
    if not relevant:
        return 0.0, []

    score = len(matched) / len(relevant)
    explanations: list[str] = []
    if matched:
        nice = ", ".join(sorted(s.replace("_", " ").title() for s in list(matched)[:5]))
        explanations.append(f"Strong skill overlap: {nice}")

    missing = relevant - user_set
    if missing and len(missing) <= 3:
        nice = ", ".join(sorted(s.replace("_", " ").title() for s in missing))
        explanations.append(f"Consider learning: {nice}")

    return round(score, 4), explanations


# ---------------------------------------------------------------------------
# 3. Resume score  (GPA + experience + projects)
# ---------------------------------------------------------------------------

def compute_resume_score(
    gpa: float = 0.0,
    experience: int = 0,
    num_projects: int = 0,
) -> tuple[float, list[str]]:
    """
    Return (score ∈ [0,1], explanations[]).

    Sub-weights: GPA 50%, experience 35%, projects 15%.
    GPA normalised on a 0-10 scale, experience capped at 10y, projects at 10.
    """
    explanations: list[str] = []

    # GPA (0-10 scale)
    gpa_norm = _normalize(gpa, 0, 10)
    if gpa >= 8:
        explanations.append(f"Excellent GPA ({gpa})")
    elif gpa >= 6:
        explanations.append(f"Good GPA ({gpa})")

    # Experience (capped at 10 years)
    exp_norm = _normalize(experience, 0, 10)
    if experience >= 2:
        explanations.append(f"{experience} years of experience strengthens your profile")

    # Projects (capped at 10)
    proj_norm = _normalize(num_projects, 0, 10)

    score = (gpa_norm * 0.50) + (exp_norm * 0.35) + (proj_norm * 0.15)
    return round(score, 4), explanations


# ---------------------------------------------------------------------------
# 4. Certifications score
# ---------------------------------------------------------------------------

def compute_certifications_score(
    user_certs: str,
    role_name: str,
) -> tuple[float, list[str]]:
    """
    Return (score ∈ [0,1], explanations[]).

    Checks overlap with role-relevant certifications and rewards count.
    """
    profile = ROLE_PROFILES.get(role_name)
    if not profile:
        return 0.0, []

    explanations: list[str] = []
    relevant_certs = profile.get("relevant_certs", [])

    # Parse user certifications string
    if isinstance(user_certs, str):
        cert_list = [c.strip().lower() for c in user_certs.split(",") if c.strip()]
    elif isinstance(user_certs, list):
        cert_list = [c.strip().lower() for c in user_certs if c.strip()]
    else:
        cert_list = []

    if not cert_list:
        return 0.0, []

    # Count relevant matches
    matched = 0
    for uc in cert_list:
        for rc in relevant_certs:
            if rc.lower() in uc or uc in rc.lower():
                matched += 1
                break

    # Score: half from count (capped at 5), half from relevance
    count_score = _normalize(len(cert_list), 0, 5)
    relevance_score = (matched / len(relevant_certs)) if relevant_certs else count_score

    score = (count_score * 0.4) + (relevance_score * 0.6)

    if matched > 0:
        explanations.append(f"{matched} relevant certification(s) for this role")
    if len(cert_list) > matched:
        explanations.append(f"{len(cert_list)} total certification(s) on your profile")

    return round(min(score, 1.0), 4), explanations


# ---------------------------------------------------------------------------
# 5. Main recommendation function
# ---------------------------------------------------------------------------

def recommend_jobs(
    ml_predictions: list[dict],
    user_degree: str = "",
    user_branch: str = "",
    user_specialization: str = "",
    user_skills: list[str] | None = None,
    user_certs: str = "",
    gpa: float = 0.0,
    experience: int = 0,
    num_projects: int = 0,
) -> list[dict]:
    """
    Re-rank ML predictions using the weighted composite score.

    Parameters
    ----------
    ml_predictions : list[dict]
        Each dict has keys: role (str), confidence (float 0-100).
    user_* : user profile fields.

    Returns
    -------
    list[dict]  sorted by final_score descending. Each dict:
        role, ml_confidence, education_score, skills_score, resume_score,
        certifications_score, final_score, explanations
    """
    if user_skills is None:
        user_skills = []

    # If no branch/specialization provided, reduce education weight and
    # redistribute to other factors for backward compatibility.
    has_education_data = bool(user_branch)
    if has_education_data:
        weights = WEIGHTS.copy()
    else:
        # Fallback: education weight goes mostly to skills and ML confidence
        weights = {
            "education": 0.15,   # degree-only matching still counts a bit
            "skills": 0.40,
            "resume": 0.25,
            "certifications": 0.10,
            "ml_boost": 0.10,    # extra weight for raw ML confidence
        }

    results = []
    for pred in ml_predictions:
        role = pred["role"]
        ml_conf = pred["confidence"] / 100.0  # normalise to 0-1

        edu_score, edu_exp = compute_education_score(
            user_degree, user_branch, user_specialization, role
        )
        skills_score, skills_exp = compute_skills_score(user_skills, role)
        resume_score, resume_exp = compute_resume_score(gpa, experience, num_projects)
        cert_score, cert_exp = compute_certifications_score(user_certs, role)

        # Composite weighted score
        final = (
            edu_score * weights["education"]
            + skills_score * weights["skills"]
            + resume_score * weights["resume"]
            + cert_score * weights["certifications"]
        )

        # If backward-compat mode, factor in raw ML confidence
        if "ml_boost" in weights:
            final += ml_conf * weights["ml_boost"]

        # Blend with ML confidence (30% ML + 70% weighted) for smoother ranking
        blended = (ml_conf * 0.30) + (final * 0.70)

        # Aggregate explanations
        all_explanations = edu_exp + skills_exp + resume_exp + cert_exp

        results.append({
            "role": role,
            "ml_confidence": round(pred["confidence"], 2),
            "education_score": round(edu_score * 100, 2),
            "skills_score": round(skills_score * 100, 2),
            "resume_score": round(resume_score * 100, 2),
            "certifications_score": round(cert_score * 100, 2),
            "final_score": round(blended * 100, 2),
            "explanations": all_explanations,
        })

    # Sort by final_score descending
    results.sort(key=lambda r: r["final_score"], reverse=True)
    return results
