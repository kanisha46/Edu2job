"""
resume_parser.py – Extract profile info from uploaded resumes.
Parses PDF and DOCX files to extract skills, degree, experience, etc.
"""

import re
import os
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known skill keywords (expandable)
# ---------------------------------------------------------------------------
KNOWN_SKILLS = [
    "python", "java", "javascript", "c++", "c#", "ruby", "go", "rust", "swift",
    "kotlin", "typescript", "php", "scala", "r", "matlab", "perl",
    "html", "css", "react", "angular", "vue", "node.js", "express",
    "django", "flask", "spring", "fastapi", "next.js",
    "sql", "mysql", "postgresql", "mongodb", "redis", "firebase", "sqlite",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
    "git", "linux", "bash", "powershell",
    "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
    "scikit-learn", "pandas", "numpy", "matplotlib", "opencv",
    "nlp", "computer vision", "data analysis", "data science",
    "excel", "power bi", "tableau",
    "rest api", "graphql", "microservices", "ci/cd", "agile", "scrum",
    "figma", "photoshop", "illustrator",
]

# ---------------------------------------------------------------------------
# Degree patterns
# ---------------------------------------------------------------------------
DEGREE_PATTERNS = [
    (r"\b(?:B\.?\s*Tech|Bachelor\s+of\s+Technology)\b", "B.Tech"),
    (r"\b(?:M\.?\s*Tech|Master\s+of\s+Technology)\b", "M.Tech"),
    (r"\b(?:B\.?\s*E\.?|Bachelor\s+of\s+Engineering)\b", "B.E"),
    (r"\b(?:M\.?\s*E\.?|Master\s+of\s+Engineering)\b", "M.E"),
    (r"\b(?:B\.?\s*Sc|Bachelor\s+of\s+Science|BSc)\b", "B.Sc"),
    (r"\b(?:M\.?\s*Sc|Master\s+of\s+Science|MSc)\b", "M.Sc"),
    (r"\b(?:BCA|Bachelor\s+of\s+Computer\s+Applications?)\b", "BCA"),
    (r"\b(?:MCA|Master\s+of\s+Computer\s+Applications?)\b", "MCA"),
    (r"\b(?:MBA|Master\s+of\s+Business\s+Admin(?:istration)?)\b", "MBA"),
    (r"\b(?:Ph\.?\s*D|Doctor\s+of\s+Philosophy)\b", "PhD"),
    (r"\b(?:B\.?\s*A\.?|Bachelor\s+of\s+Arts)\b", "B.A"),
    (r"\b(?:M\.?\s*A\.?|Master\s+of\s+Arts)\b", "M.A"),
    (r"\b(?:B\.?\s*Com|Bachelor\s+of\s+Commerce)\b", "B.Com"),
    (r"\b(?:Diploma)\b", "Diploma"),
]

# ---------------------------------------------------------------------------
# Branch / specialization patterns
# ---------------------------------------------------------------------------
BRANCH_PATTERNS = [
    (r"\b(?:Computer\s+Science|CS|CSE|C\.S\.E?\.?)\b", "Computer Science"),
    (r"\b(?:Information\s+Technology|IT|I\.T\.?)\b", "IT"),
    (r"\b(?:Electronics\s*(?:and|&)\s*Communication|ECE|E\.C\.E?\.?)\b", "ECE"),
    (r"\b(?:Electrical\s+Engineering|EE|E\.E\.?)\b", "EE"),
    (r"\b(?:Mechanical\s+Engineering|ME|M\.E\.?)\b", "ME"),
    (r"\b(?:Civil\s+Engineering)\b", "Civil"),
    (r"\b(?:Artificial\s+Intelligence|AI|AI\s*(?:/|&|and)\s*ML)\b", "AI/ML"),
    (r"\b(?:Data\s+Science|DS)\b", "Data Science"),
    (r"\b(?:Software\s+Engineering|SE)\b", "Software Engineering"),
    (r"\b(?:Electronics)\b", "Electronics"),
    (r"\b(?:Business\s+Admin|BBA)\b", "BBA"),
]

# ---------------------------------------------------------------------------
# Experience extraction
# ---------------------------------------------------------------------------
EXPERIENCE_PATTERNS = [
    r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp\.?)",
    r"(?:experience|exp\.?)\s*(?:of\s+)?(\d+)\+?\s*(?:years?|yrs?)",
    r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:in|of|working)",
]

# ---------------------------------------------------------------------------
# GPA / CGPA extraction
# ---------------------------------------------------------------------------
GPA_PATTERNS = [
    r"(?:GPA|CGPA|C\.G\.P\.A\.?)[\s:]*(\d\.?\d*)",
    r"(\d\.\d+)\s*(?:/\s*(?:10|4\.0|4))",
]

# ---------------------------------------------------------------------------
# Certification patterns
# ---------------------------------------------------------------------------
CERT_KEYWORDS = [
    "aws certified", "azure certified", "google cloud certified",
    "pmp", "scrum master", "csm", "comptia", "cisco", "ccna", "ccnp",
    "oracle certified", "certified kubernetes", "cka", "ckad",
    "data science certification", "machine learning certification",
    "deep learning specialization", "tensorflow developer",
    "certified ethical hacker", "ceh", "cissp", "oscp",
]


def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    try:
        import PyPDF2
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except ImportError:
        logger.warning("PyPDF2 not installed. Install it: pip install PyPDF2")
        return ""
    except Exception as e:
        logger.error(f"PDF parsing failed: {e}")
        return ""


def extract_text_from_docx(file_path):
    """Extract text from a DOCX file."""
    try:
        import docx
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except ImportError:
        logger.warning("python-docx not installed. Install it: pip install python-docx")
        return ""
    except Exception as e:
        logger.error(f"DOCX parsing failed: {e}")
        return ""


def extract_text(file_path):
    """Extract text based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""


def extract_skills(text):
    """Find known skills in the resume text."""
    text_lower = text.lower()
    found = []
    for skill in KNOWN_SKILLS:
        # Use word boundary matching for short skills, contains for longer ones
        if len(skill) <= 2:
            if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
                found.append(skill.title() if len(skill) > 1 else skill.upper())
        else:
            if skill in text_lower:
                found.append(skill.title())
    return list(dict.fromkeys(found))  # Deduplicate while preserving order


def extract_degree(text):
    """Find the highest degree mentioned."""
    for pattern, label in DEGREE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return ""


def extract_branch(text):
    """Find the educational branch / specialization."""
    for pattern, label in BRANCH_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return ""


def extract_experience(text):
    """Extract years of experience."""
    for pattern in EXPERIENCE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return 0


def extract_gpa(text):
    """Extract GPA/CGPA."""
    for pattern in GPA_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            gpa = float(match.group(1))
            if gpa <= 10:
                return gpa
    return 0.0


def extract_certifications(text):
    """Find certifications mentioned."""
    text_lower = text.lower()
    found = []
    for cert in CERT_KEYWORDS:
        if cert in text_lower:
            found.append(cert.title())
    return found


def extract_name(text):
    """Try to extract candidate name (first line heuristic)."""
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if lines:
        first_line = lines[0]
        # If first line is short and looks like a name (no numbers, no @)
        if len(first_line) < 50 and "@" not in first_line and not re.search(r"\d", first_line):
            return first_line
    return ""


def parse_resume(file_path):
    """
    Main entry point: parse a resume file and return extracted profile data.
    Returns a dict with keys: skills, degree, gpa, experience, certifications, name
    """
    text = extract_text(file_path)
    if not text.strip():
        return {"error": "Could not extract text from the file."}

    skills = extract_skills(text)
    degree = extract_degree(text)
    branch = extract_branch(text)
    experience = extract_experience(text)
    gpa = extract_gpa(text)
    certs = extract_certifications(text)
    name = extract_name(text)

    result = {
        "name": name,
        "degree": degree,
        "branch": branch,
        "skills": skills,
        "gpa": gpa,
        "experience": experience,
        "certifications": ", ".join(certs),
        "raw_text_preview": text[:500],  # First 500 chars for debugging
    }

    logger.info(f"Resume parsed: degree={degree}, branch={branch}, skills={len(skills)}, exp={experience}y, gpa={gpa}")
    return result
