import React, { useEffect, useState } from 'react';
import Sidebar from '../components/Sidebar';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { getUser, apiGet, apiPost } from '../utils/api';
import { motion } from 'framer-motion';
import './Quiz.css';

const Quiz = () => {
  const [searchParams] = useSearchParams();
  const subject = searchParams.get('subject');
  const engine = searchParams.get('engine'); // 'new' for quiz_engine, null for old quiz
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [quizData, setQuizData] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [feedback, setFeedback] = useState('');
  const [completed, setCompleted] = useState(false);
  const [score, setScore] = useState(0);
  const [total, setTotal] = useState(15);

  useEffect(() => {
    if (!getUser()) { navigate('/login'); return; }
    if (!subject) { navigate('/interview'); return; }

    const loadQuiz = async () => {
      try {
        // Use new quiz engine or old quiz endpoint
        const endpoint = engine === 'new'
          ? `/quiz-engine/quiz/${subject}`
          : `/quiz/${subject}`;

        const res = await apiGet(endpoint);
        if (res.error) {
          setError(res.error);
        } else {
          setQuizData(res);
          setTotal(res.total || res.questions?.length || 15);
        }
      } catch (e) {
        setError('Failed to load quiz');
      } finally {
        setLoading(false);
      }
    };
    loadQuiz();
  }, [subject, engine, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!quizData) return;

    let calculatedScore = 0;
    const formData = new FormData(e.target);

    quizData.questions.forEach(q => {
      const selected = formData.get(`q_${q.id}`);
      if (selected === q.ans) calculatedScore++;
    });

    setScore(calculatedScore);
    setCompleted(true);

    try {
      const submitEndpoint = engine === 'new' ? '/quiz-engine/submit' : '/quiz/submit';
      const res = await apiPost(submitEndpoint, {
        subject: quizData.subject || subject,
        score: calculatedScore,
        total: quizData.questions.length,
        date: new Date().toLocaleDateString('en-GB')
      });

      if (res.feedback) setFeedback(res.feedback);
      else {
        const pct = (calculatedScore / quizData.questions.length) * 100;
        setFeedback(pct > 70 ? 'Good job! You have a strong grasp of this subject.' : 'Keep practicing! Review the topics and try again.');
      }
      setSuccess('Score recorded!');
    } catch (err) {
      setError('Could not record score');
    }
  };

  const containerVars = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };
  const itemVars = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 200 } }
  };

  return (
    <div className="app-layout">
      <Sidebar activePage="interview" />

      <div className="main-content">
        <header className="main-header">
          <h2>Quiz Arena</h2>
          <div className="header-actions">
            <div className="header-avatar" id="headerAvatar">
              {getUser()?.full_name?.charAt(0)?.toUpperCase()}
            </div>
          </div>
        </header>

        <div className="page-content quiz-container-inner-epic">
          {(error || success) && (
            <motion.div initial={{opacity:0, y:-10}} animate={{opacity:1, y:0}} className={`toast-epic toast-${error ? 'error' : 'success'}`}>
              <span className="material-symbols-outlined">{error ? 'error' : 'check_circle'}</span>
              {error || success}
            </motion.div>
          )}

          {loading && (
            <div className="loading-container-epic">
              <div className="spinner-epic"><span className="material-symbols-outlined spinner-icon-epic">sync</span></div>
              <p>Loading quiz...</p>
            </div>
          )}

          {!loading && quizData && !completed && (
            <motion.form onSubmit={handleSubmit} variants={containerVars} initial="hidden" animate="visible" className="quiz-form-epic">
              <motion.div className="quiz-header-top-epic" variants={itemVars}>
                <div className="quiz-title-main-epic">{quizData.subject || subject} Test</div>
                <div className="quiz-meta-epic">{quizData.questions.length} Questions</div>
              </motion.div>
              
              <div className="questions-wrapper-epic">
                {quizData.questions.map((q, index) => (
                  <motion.div className="question-card-epic" key={q.id} variants={itemVars}>
                    <div className="question-text-epic">{index + 1}. {q.q}</div>
                    <div className="options-grid-epic">
                      {q.options.map((opt, optIdx) => (
                        <label className="option-label-epic" key={optIdx}>
                          <input type="radio" name={`q_${q.id}`} value={opt} required className="option-input-epic" />
                          <span className="custom-radio"></span>
                          {opt}
                        </label>
                      ))}
                    </div>
                  </motion.div>
                ))}
              </div>
              
              <motion.button type="submit" className="btn btn-primary btn-epic-full" variants={itemVars}>
                <span className="material-symbols-outlined">send</span> Submit Answers
              </motion.button>
            </motion.form>
          )}

          {completed && quizData && (
            <motion.div className="result-section-epic" initial={{scale:0.9, opacity:0}} animate={{scale:1, opacity:1}} transition={{type: 'spring', stiffness: 200, damping: 20}}>
              <div className="result-glow-epic"></div>
              <h2 className="result-title-epic">Quiz Completed!</h2>
              <div className="score-circle-epic">
                <div className="score-ring"></div>
                <span>{score}</span>
              </div>
              <p className="score-text-epic">
                You scored <b>{score}</b> out of <b>{quizData.questions.length}</b>
              </p>
              {feedback && (
                <p className="feedback-text">{feedback}</p>
              )}
              <div className="result-actions-epic">
                <Link to="/dashboard" className="btn btn-epic-glass"><span className="material-symbols-outlined">dashboard</span> Dashboard</Link>
                <Link to="/interview" className="btn btn-epic-primary"><span className="material-symbols-outlined">replay</span> More Tests</Link>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Quiz;
