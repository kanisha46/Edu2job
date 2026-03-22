"""
skill_gap.py – Skill Gap Analysis & Learning Recommendations.

Compares a user's current skills against the required skills for a
target role and suggests learning topics for each missing skill.

Uses ROLE_PROFILES from recommendation.py to avoid duplication.
"""

import logging
from flask import Blueprint, request, jsonify, g
from auth import token_required
from recommendation import ROLE_PROFILES

logger = logging.getLogger(__name__)

skill_gap_bp = Blueprint("skill_gap", __name__, url_prefix="/skillgap")

# ---------------------------------------------------------------------------
# Skill name formatting – handles acronyms (.title() turns "sql" → "Sql")
# ---------------------------------------------------------------------------
_ACRONYMS = {
    "sql": "SQL", "html": "HTML", "css": "CSS", "api": "API", "apis": "APIs",
    "aws": "AWS", "gcp": "GCP", "ci/cd": "CI/CD", "devops": "DevOps",
    "nosql": "NoSQL", "oop": "OOP", "dbms": "DBMS", "os": "OS",
    "tcp/ip": "TCP/IP", "osi": "OSI", "jvm": "JVM", "rest": "REST",
    "graphql": "GraphQL", "mongodb": "MongoDB", "mysql": "MySQL",
    "postgresql": "PostgreSQL", "javascript": "JavaScript",
    "typescript": "TypeScript", "node.js": "Node.js", "next.js": "Next.js",
    "react.js": "React.js", "vue.js": "Vue.js", "fastapi": "FastAPI",
    "pytorch": "PyTorch", "tensorflow": "TensorFlow", "numpy": "NumPy",
    "scipy": "SciPy", "opencv": "OpenCV", "nlp": "NLP",
}


def _format_skill_name(raw: str) -> str:
    """Format a skill key like 'machine_learning' to display name 'Machine Learning'."""
    clean = raw.replace("_", " ").strip()
    # Check the whole phrase first
    if clean.lower() in _ACRONYMS:
        return _ACRONYMS[clean.lower()]
    # Otherwise title-case but fix known acronyms word-by-word
    words = clean.split()
    result = []
    for w in words:
        lower = w.lower()
        if lower in _ACRONYMS:
            result.append(_ACRONYMS[lower])
        else:
            result.append(w.capitalize())
    return " ".join(result)


# ---------------------------------------------------------------------------
# Learning recommendations: skill → suggested sub-topics / modules
# ---------------------------------------------------------------------------
LEARNING_RECOMMENDATIONS = {
    # Programming & Development
    "python": ["Core Python Syntax", "Data Structures in Python", "OOP in Python", "File Handling & Modules"],
    "java": ["Core Java & OOP", "Collections Framework", "Exception Handling", "Multithreading Basics"],
    "javascript": ["ES6+ Features", "DOM Manipulation", "Async/Await & Promises", "Event Handling"],
    "typescript": ["Type Annotations", "Interfaces & Generics", "TypeScript with React", "Advanced Types"],
    "sql": ["SELECT & Joins", "Aggregations & Grouping", "Subqueries", "Database Normalization"],
    "html": ["Semantic HTML5", "Forms & Validation", "Accessibility Basics", "SEO-friendly Markup"],
    "css": ["Flexbox & Grid", "Responsive Design", "CSS Variables", "Animations & Transitions"],

    # Frameworks & Libraries
    "react": ["Components & Props", "Hooks (useState, useEffect)", "React Router", "State Management"],
    "angular": ["Components & Modules", "Services & DI", "Routing", "RxJS Observables"],
    "vue": ["Vue Components", "Vue Router", "Vuex State Management", "Composition API"],
    "next.js": ["Pages & Routing", "SSR vs SSG", "API Routes", "Data Fetching"],
    "node.js": ["Express.js Basics", "REST API Design", "Middleware", "File System & Streams"],
    "django": ["Models & ORM", "Views & Templates", "URL Routing", "Django REST Framework"],
    "flask": ["Routes & Blueprints", "Jinja2 Templates", "Request Handling", "Flask Extensions"],
    "spring": ["Spring Boot Basics", "Dependency Injection", "REST APIs with Spring", "Spring Data JPA"],
    "fastapi": ["Path & Query Parameters", "Pydantic Models", "Async Endpoints", "Dependency Injection"],

    # Data & ML
    "machine_learning": ["Supervised Learning", "Regression & Classification", "Model Evaluation", "Feature Engineering"],
    "tensorflow": ["Tensors & Operations", "Building Neural Networks", "Training & Evaluation", "Model Saving & Loading"],
    "pytorch": ["Tensors in PyTorch", "Autograd & Backpropagation", "Building Models", "Training Loops"],
    "pandas": ["DataFrames & Series", "Data Cleaning", "Groupby & Aggregations", "Merging & Joining"],
    "numpy": ["Array Operations", "Broadcasting", "Linear Algebra", "Random Number Generation"],
    "data_analysis": ["Exploratory Data Analysis", "Data Visualization", "Statistical Measures", "Handling Missing Data"],
    "data_science": ["Data Wrangling", "Statistical Analysis", "Visualization with Matplotlib", "Hypothesis Testing"],
    "keras": ["Sequential Models", "Layers & Activations", "Callbacks", "Transfer Learning"],
    "scikit-learn": ["Preprocessing", "Classification Algorithms", "Model Selection", "Pipeline Building"],

    # DevOps & Cloud
    "docker": ["Containers & Images", "Dockerfile Basics", "Docker Compose", "Volume & Networking"],
    "kubernetes": ["Pods & Deployments", "Services & Ingress", "ConfigMaps & Secrets", "Scaling"],
    "aws": ["EC2 & S3 Basics", "IAM & Security", "Lambda Functions", "CloudFormation"],
    "azure": ["Azure VMs", "Azure Functions", "Blob Storage", "Azure DevOps"],
    "gcp": ["Compute Engine", "Cloud Functions", "Cloud Storage", "BigQuery"],
    "terraform": ["HCL Syntax", "Providers & Resources", "State Management", "Modules"],
    "jenkins": ["Pipeline Basics", "Jenkinsfile", "Plugins", "CI/CD Workflows"],
    "linux": ["File System & Commands", "Permissions", "Shell Scripting", "Process Management"],
    "bash": ["Script Basics", "Variables & Loops", "Text Processing", "Automation"],
    "ci/cd": ["Pipeline Concepts", "Automated Testing", "Deployment Strategies", "Monitoring"],
    "git": ["Branching & Merging", "Rebase vs Merge", "Pull Requests", "Git Workflows"],

    # Databases
    "mongodb": ["Documents & Collections", "CRUD Operations", "Indexing", "Aggregation Pipeline"],
    "postgresql": ["Tables & Schemas", "Advanced Queries", "Indexing", "Transactions"],

    # Design & Other
    "figma": ["Frames & Components", "Auto Layout", "Prototyping", "Design Systems"],
    "autocad": ["2D Drafting", "3D Modeling Basics", "Layers & Blocks", "Printing & Plotting"],
    "solidworks": ["Part Design", "Assembly", "Drawings", "Sheet Metal"],
    "matlab": ["Matrix Operations", "Plotting", "Simulink Basics", "Control Systems"],
    "ansys": ["FEA Basics", "Mesh Generation", "Boundary Conditions", "Post-processing"],

    # Soft Skills & Business
    "communication": ["Technical Writing", "Presentation Skills", "Active Listening", "Email Etiquette"],
    "management": ["Team Leadership", "Project Planning", "Agile Methodology", "Stakeholder Communication"],
    "finance": ["Financial Statements", "Budgeting", "Investment Basics", "Risk Management"],
    "marketing": ["Digital Marketing", "SEO Basics", "Content Strategy", "Social Media Marketing"],
    "sales": ["Sales Funnel", "Negotiation Skills", "CRM Tools", "Lead Generation"],
    "excel": ["Formulas & Functions", "Pivot Tables", "Data Visualization", "VBA Macros"],
    "power bi": ["Data Modeling", "DAX Fundamentals", "Dashboard Design", "Data Refresh"],
    "tableau": ["Connecting Data Sources", "Building Visualizations", "Calculated Fields", "Dashboard Design"],
}

# ---------------------------------------------------------------------------
# Core function: analyze_skill_gap
# ---------------------------------------------------------------------------

def analyze_skill_gap(user_skills: list[str], target_role: str) -> dict:
    """
    Compare user skills against required skills for a target role.

    Returns dict with:
        target_role, matched_skills, missing_skills, match_percentage,
        learning_path (list of {skill, topics} for each missing skill)
    """
    # --- Validate target_role ---
    profile = ROLE_PROFILES.get(target_role)
    if not profile:
        return {
            "error": f"Unknown role: '{target_role}'. Please select a valid role.",
            "available_roles": list(ROLE_PROFILES.keys()),
        }

    # --- Normalize skills: lowercase, strip, deduplicate ---
    if not user_skills or (len(user_skills) == 1 and not user_skills[0].strip()):
        all_required = list(profile["relevant_skills"])
        formatted = [_format_skill_name(s) for s in all_required]
        return {
            "target_role": target_role,
            "message": "No skills provided. Please add skills in your profile first.",
            "matched_skills": [],
            "missing_skills": formatted,
            "match_percentage": 0,
            "learning_path": _build_learning_path(all_required),
        }

    user_set = set(
        s.strip().lower().replace(" ", "_")
        for s in user_skills
        if s.strip()
    )

    required_set = set(
        s.strip().lower().replace(" ", "_")
        for s in profile["relevant_skills"]
    )

    # --- Compute matched and missing ---
    matched = sorted(required_set & user_set)
    missing = sorted(required_set - user_set)

    # --- Percentage (rounded to nearest integer) ---
    if required_set:
        match_pct = round((len(matched) / len(required_set)) * 100)
    else:
        match_pct = 100

    # --- Build learning path for missing skills ---
    learning_path = _build_learning_path(missing)

    return {
        "target_role": target_role,
        "matched_skills": [_format_skill_name(s) for s in matched],
        "missing_skills": [_format_skill_name(s) for s in missing],
        "match_percentage": match_pct,
        "learning_path": learning_path,
    }


def _build_learning_path(missing_skills: list[str]) -> list[dict]:
    """Build learning recommendations for each missing skill."""
    path = []
    for skill in missing_skills:
        normalized = skill.strip().lower().replace(" ", "_")
        topics = LEARNING_RECOMMENDATIONS.get(normalized, [f"Fundamentals of {_format_skill_name(skill)}"])
        path.append({
            "skill": _format_skill_name(skill),
            "topics": topics,
        })
    return path


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@skill_gap_bp.route("/roles", methods=["GET"])
@token_required
def get_roles():
    """Return list of all available target roles."""
    roles = list(ROLE_PROFILES.keys())
    return jsonify({"roles": roles}), 200


@skill_gap_bp.route("/analyze", methods=["POST"])
@token_required
def analyze():
    """Analyze skill gap for given target_role and user skills."""
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    target_role = data.get("target_role", "").strip()
    skills_input = data.get("skills", "")

    # Parse skills from string or list
    if isinstance(skills_input, str):
        user_skills = [s.strip() for s in skills_input.split(",") if s.strip()]
    elif isinstance(skills_input, list):
        user_skills = [s.strip() for s in skills_input if s.strip()]
    else:
        user_skills = []

    if not target_role:
        return jsonify({"error": "Please select a target role."}), 400

    result = analyze_skill_gap(user_skills, target_role)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result), 200
