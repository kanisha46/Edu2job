# Edu2Job – AI Career Prediction Platform

Edu2Job is a premium, full-stack AI platform designed to bridge the gap between education and employment. It utilizes machine learning to analyze user skills and resumes, providing statistical job role predictions and interactive skill-gap visualizations.

The dataset was augmented with domain-specific entries to reduce bias toward technical roles and improve prediction coverage.

## ✨ Features

- **Premium UI/UX**: Ultra-modern, high-density design with glassmorphism, glowing accents, and fluid animations.
- **Global Theme System**: Seamless toggle between "Professional Light" and "Dark Universe" themes with persistent user preference.
- **AI Career Prediction**: Parallel execution of multiple ML models (Random Forest, Logistic Regression) to predict the most likely job roles.
- **Skill Gap Intelligence**: Interactive node mapping that identifies precisely which skills you need to acquire for your target role.
- **Mock Test Arenas**: Adaptive, subject-specific technical tests with real-time scoring and AI-profile syncing.
- **Intelligent Resume Parsing**: Automatic skill extraction from PDF and DOCX uploads using advanced parsing logic.
- **Identity Matrix (Profile)**: Comprehensive management of your professional profile, skills, and experience with a futuristic UI.

## 🛠 Tech Stack

### Frontend
- **System**: [React 19](https://react.dev/) + [Vite 8](https://vitejs.dev/)
- **Animations**: [Framer Motion](https://www.framer.com/motion/) (Spring physics, stagger effects, glassmorphic transitions)
- **Typography**: [React Type Animation](https://www.npmjs.com/package/react-type-animation) (Dynamic hero text)
- **Styling**: Vanilla CSS with a strict CSS Variable architecture for global theming.
- **Icons**: [Google Material Symbols](https://fonts.google.com/icons)

### Backend
- **Core**: Python 3.8+ / [Flask](https://flask.palletsprojects.com/)
- **Database**: [MongoDB](https://www.mongodb.com/) (with an automated in-memory fallback for zero-config testing)
- **Machine Learning**: Scikit-Learn (Random Forest, Logistic Regression), Pandas, Numpy
- **Security**: JWT (JSON Web Tokens) for stateless authentication.

## 📂 Project Structure

```text
Edu2Job/
├── backend/                # Flask API & ML Logic
│   ├── app.py              # Main Entry Point
│   ├── auth.py             # JWT & Auth Logic
│   ├── prediction.py       # ML Model Inference
│   ├── resume_parser.py    # PDF/DOCX Parsing
│   └── train_model.py      # Model Training Script
├── frontend/               # React + Vite Frontend
│   ├── src/
│   │   ├── components/     # Reusable UI (Sidebar, Navbar)
│   │   ├── context/        # Global State (ThemeContext)
│   │   ├── pages/          # Feature Pages (Dashboard, SkillGap, Quiz)
│   │   └── utils/          # API & Helper functions
│   └── index.html          # Entry Template
├── ml_model/               # Pre-trained ML Models (*.pkl)
└── dataset/                # Training data for Career Predictions
```

## 🚀 Getting Started

### Prerequisites
- **Python 3.8+**
- **Node.js 18+**
- (Optional) **MongoDB** (App falls back to in-memory DB if not found)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/Edu2Job.git
   cd Edu2Job
   ```

2. **Setup Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python app.py
   ```

3. **Setup Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access**:
   - Backend API: `http://localhost:5000`
   - Frontend: `http://localhost:5173`

## 📡 API Overview
- `POST /auth/login` - Secure user authentication.
- `POST /api/predict` - Run the ML Prediction Engine.
- `POST /api/skill-gap` - Analyze missing expertise for target roles.
- `POST /api/user/upload-resume` - Pulse-parse uploaded documents for skills.

## 📄 License
This project is licensed under the MIT License.
