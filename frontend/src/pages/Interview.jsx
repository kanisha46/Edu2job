import React, { useEffect, useState } from 'react';
import Sidebar from '../components/Sidebar';
import { Link, useNavigate } from 'react-router-dom';
import { getUser, apiGet } from '../utils/api';
import { motion } from 'framer-motion';
import './Interview.css';

const SUBJECT_COLORS = [
  { bg: 'rgba(108, 99, 255, 0.15)', border: 'rgba(108, 99, 255, 0.3)', text: '#6C63FF' },
  { bg: 'rgba(168, 85, 247, 0.15)', border: 'rgba(168, 85, 247, 0.3)', text: '#A855F7' },
  { bg: 'rgba(34, 197, 94, 0.15)', border: 'rgba(34, 197, 94, 0.3)', text: '#22C55E' },
  { bg: 'rgba(251, 191, 36, 0.15)', border: 'rgba(251, 191, 36, 0.3)', text: '#FBBf24' },
  { bg: 'rgba(59, 130, 246, 0.15)', border: 'rgba(59, 130, 246, 0.3)', text: '#3B82F6' },
];

const Interview = () => {
  const navigate = useNavigate();
  const user = getUser();
  const [selectedBranch, setSelectedBranch] = useState('');
  const [branches, setBranches] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user) { navigate('/login'); return; }

    // Load branches
    const loadBranches = async () => {
      try {
        const res = await apiGet('/quiz-engine/branches');
        if (res.branches) setBranches(res.branches);
      } catch (e) { /* silent */ }
    };
    loadBranches();

    // Pre-select user's branch
    if (user.branch) setSelectedBranch(user.branch);
  }, []);

  // Load subjects when branch changes
  useEffect(() => {
    if (!selectedBranch) { setSubjects([]); return; }

    const loadSubjects = async () => {
      setLoading(true);
      try {
        const res = await apiGet(`/quiz-engine/subjects/${encodeURIComponent(selectedBranch)}`);
        if (res.subjects) setSubjects(res.subjects);
      } catch (e) { setSubjects([]); }
      setLoading(false);
    };
    loadSubjects();
  }, [selectedBranch]);

  const containerVars = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.12 } }
  };
  const itemVars = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 300 } }
  };

  return (
    <div className="app-layout">
      <Sidebar activePage="interview" />

      <div className="main-content">
        <header className="main-header">
          <h2>Interview Intelligence</h2>
          <div className="header-actions">
            <div className="header-avatar" id="headerAvatar">
              {user?.full_name?.charAt(0)?.toUpperCase()}
            </div>
          </div>
        </header>

        <div className="page-content">
          <motion.div initial="hidden" animate="visible" variants={containerVars}>
            <motion.h3 className="subject-title-epic" variants={itemVars}>Technical Mock Tests</motion.h3>
            <motion.p className="page-subtitle-epic" variants={itemVars}>
              Select your department and test your knowledge with subject-specific quizzes. Scores are saved to your profile.
            </motion.p>

            {/* Branch Selector */}
            <motion.div className="branch-selector-section" variants={itemVars}>
              <label className="branch-label">Your Department</label>
              <div className="select-wrapper branch-select-wrap">
                <select
                  className="epic-input branch-select"
                  value={selectedBranch}
                  onChange={e => setSelectedBranch(e.target.value)}
                >
                  <option value="">Select your branch...</option>
                  {branches.map(b => (
                    <option key={b} value={b}>{b}</option>
                  ))}
                </select>
                <span className="material-symbols-outlined dropdown-icon">expand_more</span>
              </div>
            </motion.div>

            {/* No branch selected */}
            {!selectedBranch && (
              <motion.div className="empty-state-interview" variants={itemVars}>
                <span className="material-symbols-outlined">school</span>
                <h4>Select your department to view available tests</h4>
                <p>Choose your branch above and we'll show subject-specific mock tests tailored for your department.</p>
              </motion.div>
            )}

            {/* Loading */}
            {loading && (
              <div className="loading-container-epic">
                <div className="spinner-epic">
                  <span className="material-symbols-outlined spinner-icon-epic">sync</span>
                </div>
                <p>Loading subjects...</p>
              </div>
            )}

            {/* Subject Cards */}
            {!loading && subjects.length > 0 && (
              <motion.div className="subjects-grid-epic" variants={containerVars}>
                {subjects.map((sub, i) => {
                  const color = SUBJECT_COLORS[i % SUBJECT_COLORS.length];
                  return (
                    <motion.div className="subject-card-epic" key={sub.key} variants={itemVars} whileHover={{ y: -8, scale: 1.02 }}>
                      <div className="subject-glow-epic" style={{ background: color.bg }}></div>
                      <div className="subject-header-epic">
                        <div className="subject-icon-box-epic" style={{ color: color.text, background: color.bg, borderColor: color.border }}>
                          <span className="material-symbols-outlined">{sub.icon}</span>
                        </div>
                        <h3 className="subject-title-epic">{sub.name}</h3>
                      </div>
                      <p className="subject-desc-epic">{sub.desc}</p>
                      <div className="subject-meta">
                        <span className="material-symbols-outlined">quiz</span> 15 Questions · MCQ
                      </div>
                      <div className="subject-actions-epic">
                        <Link to={`/quiz?subject=${sub.key}&engine=new`} className="btn-start-epic">
                          Start Test
                        </Link>
                      </div>
                    </motion.div>
                  );
                })}
              </motion.div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Interview;