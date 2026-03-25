"""
train_model.py – Generate synthetic dataset + train ML models.

Usage:
    python train_model.py

Produces:
    dataset/jobs_dataset.csv
    ml_model/model.pkl
    ml_model/scaler.pkl
    ml_model/encoder_degree.pkl
    ml_model/encoder_role.pkl
    ml_model/feature_columns.pkl
"""

import os
import random
import logging

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "..", "dataset")
MODEL_DIR = os.path.join(BASE_DIR, "..", "ml_model")
DATASET_PATH = os.path.join(DATASET_DIR, "jobs_dataset.csv")


# ---------------------------------------------------------------------------
# 1. Generate synthetic dataset
# ---------------------------------------------------------------------------
def generate_dataset(num_samples: int = 1200) -> str:
    np.random.seed(42)
    random.seed(42)

    degrees = ["B.Tech", "M.Tech", "B.Sc", "M.Sc", "BCA", "MCA", "B.E", "MBA"]
    branches = [
        "Computer Science", "IT", "ECE", "EE", "ME",
        "Civil", "AI/ML", "Data Science", "BBA", "MBA", "Chemical", "Other",
    ]
    job_roles = [
        "Software Engineer", "Data Scientist", "Frontend Developer",
        "Backend Developer", "DevOps Engineer", "ML Engineer",
        "Full Stack Developer", "Cloud Architect",
        "Mechanical Engineer", "Civil Engineer", "Electrical Engineer",
        "Business Analyst", "HR Manager", "Marketing Executive",
        "Chemical Engineer"
    ]
    all_skills = [
        "python", "java", "javascript", "react", "sql",
        "aws", "docker", "machine_learning",
        "autocad", "solidworks", "ansys", "matlab", "plc", "scada",
        "management", "marketing", "finance", "communication", "sales",
        "chemistry", "process_engineering", "hysys", "thermodynamics"
    ]

    # Skill-to-role affinity mapping for realistic patterns
    role_skill_map = {
        "Software Engineer":      ["java", "python", "sql"],
        "Data Scientist":         ["python", "machine_learning", "sql"],
        "Frontend Developer":     ["javascript", "react"],
        "Backend Developer":      ["python", "java", "sql", "docker"],
        "DevOps Engineer":        ["aws", "docker", "python"],
        "ML Engineer":            ["python", "machine_learning", "aws"],
        "Full Stack Developer":   ["javascript", "react", "python", "sql"],
        "Cloud Architect":        ["aws", "docker", "python"],
        "Mechanical Engineer":    ["autocad", "solidworks", "matlab", "ansys"],
        "Civil Engineer":         ["autocad", "ansys", "management"],
        "Electrical Engineer":    ["matlab", "plc", "scada", "autocad"],
        "Business Analyst":       ["sql", "communication", "management", "finance"],
        "HR Manager":             ["communication", "management"],
        "Marketing Executive":    ["marketing", "communication", "management", "sales"],
        "Chemical Engineer":      ["chemistry", "process_engineering", "hysys", "thermodynamics", "matlab"],
    }

    # Branch-to-role affinity mapping for realistic patterns
    role_branch_map = {
        "Software Engineer":      ["Computer Science", "IT", "AI/ML", "ECE"],
        "Data Scientist":         ["Computer Science", "Data Science", "AI/ML", "IT"],
        "Frontend Developer":     ["Computer Science", "IT"],
        "Backend Developer":      ["Computer Science", "IT", "ECE"],
        "DevOps Engineer":        ["Computer Science", "IT"],
        "ML Engineer":            ["Computer Science", "AI/ML", "Data Science"],
        "Full Stack Developer":   ["Computer Science", "IT"],
        "Cloud Architect":        ["Computer Science", "IT"],
        "Mechanical Engineer":    ["ME", "Other"],
        "Civil Engineer":         ["Civil", "Other"],
        "Electrical Engineer":    ["EE", "ECE"],
        "Business Analyst":       ["MBA", "BBA", "IT", "Computer Science"],
        "HR Manager":             ["MBA", "BBA", "Other"],
        "Marketing Executive":    ["MBA", "BBA", "Other"],
        "Chemical Engineer":      ["Chemical", "Other"],
    }

    rows = []
    for _ in range(num_samples):
        role = random.choice(job_roles)
        degree = random.choice(degrees)
        gpa = round(random.uniform(5.5, 10.0), 2)

        # Pick a branch that matches the role most of the time (80%),
        # else a random branch for noise
        if random.random() < 0.80:
            branch = random.choice(role_branch_map[role])
        else:
            branch = random.choice(branches)

        skills = {s: 0 for s in all_skills}
        for s in role_skill_map[role]:
            skills[s] = 1
        # Add noise
        for s in all_skills:
            if random.random() < 0.15:
                skills[s] = 1 - skills[s]

        row = {
            "degree": degree,
            "branch": branch,
            "gpa": gpa,
            "num_certs": random.randint(0, 5),
            "num_projects": random.randint(1, 8),
            "num_internships": random.randint(0, 3),
            "job_role": role,
        }
        row.update(skills)
        rows.append(row)

    df = pd.DataFrame(rows)
    os.makedirs(DATASET_DIR, exist_ok=True)
    df.to_csv(DATASET_PATH, index=False)
    logger.info(f"Dataset saved → {DATASET_PATH} ({len(df)} rows)")
    return DATASET_PATH


# ---------------------------------------------------------------------------
# 2. Train models
# ---------------------------------------------------------------------------
def train(dataset_path: str):
    df = pd.read_csv(dataset_path)
    logger.info(f"Loaded dataset: {df.shape}")

    # Handle missing values
    df = df.fillna(0)

    # Encode degree
    le_degree = LabelEncoder()
    df["degree_encoded"] = le_degree.fit_transform(df["degree"])

    # Encode branch
    le_branch = LabelEncoder()
    df["branch_encoded"] = le_branch.fit_transform(df["branch"])

    # Encode target
    le_role = LabelEncoder()
    y = le_role.fit_transform(df["job_role"])

    # Features (drop raw text columns and target)
    X = df.drop(columns=["degree", "branch", "job_role"])
    feature_columns = list(X.columns)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Candidate models
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=150, random_state=42),
    }

    best_name = None
    best_acc = 0
    best_model = None

    for name, model in models.items():
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        acc = accuracy_score(y_test, y_pred)
        logger.info(f"{name}: accuracy = {acc:.4f}")
        logger.info(f"\n{classification_report(y_test, y_pred, target_names=le_role.classes_, zero_division=0)}")

        if acc > best_acc:
            best_acc = acc
            best_name = name
            best_model = model

    logger.info(f"\n✅ Best model: {best_name} (accuracy: {best_acc:.4f})")

    # Save artifacts
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(best_model,       os.path.join(MODEL_DIR, "model.pkl"))
    joblib.dump(scaler,           os.path.join(MODEL_DIR, "scaler.pkl"))
    joblib.dump(le_degree,        os.path.join(MODEL_DIR, "encoder_degree.pkl"))
    joblib.dump(le_branch,        os.path.join(MODEL_DIR, "encoder_branch.pkl"))
    joblib.dump(le_role,          os.path.join(MODEL_DIR, "encoder_role.pkl"))
    joblib.dump(feature_columns,  os.path.join(MODEL_DIR, "feature_columns.pkl"))
    logger.info(f"Model artifacts saved → {MODEL_DIR}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # path = generate_dataset()
    path = DATASET_PATH
    train(path)
    logger.info("Training complete. You can now start the server with: python app.py")
