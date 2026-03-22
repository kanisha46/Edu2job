import React, { useEffect, useState } from 'react';
import Sidebar from '../components/Sidebar';
import { useNavigate } from 'react-router-dom';
import { getUser, apiGet, apiPost } from '../utils/api';
import { motion } from 'framer-motion';
import './SkillGap.css';

const SkillGap = () => {
  const navigate = useNavigate();
  const [roles, setRoles] = useState([]);
  const [selectedRole, setSelectedRole] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const user = getUser();

  useEffect(() => {
    if (!user) { navigate('/login'); return; }

    // Load available roles
    const loadRoles = async () => {
      try {
        const res = await apiGet('/skillgap/roles');
        if (res.roles) setRoles(res.roles);
      } catch (e) { /* silent */ }
    };
    loadRoles();

    // Pre-select target_role if saved in profile
    if (user.target_role) {
      setSelectedRole(user.target_role);
    }
  }, []);

  // Auto-analyze when role changes
  useEffect(() => {
    if (selectedRole) analyzeGap();
  }, [selectedRole]);

  const analyzeGap = async () => {
    if (!selectedRole) return;
    setLoading(true);
    setError('');
    setAnalysis(null);

    try {
      const res = await apiPost('/skillgap/analyze', {
        target_role: selectedRole,
        skills: user?.skills || '',
      });

      if (res.error) {
        setError(res.error);
      } else {
        setAnalysis(res);
      }
    } catch (e) {
      setError('Failed to analyze skill gap.');
    } finally {
      setLoading(false);
    }
  };

  const staggerVars = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };
  const cardVars = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 200 } }
  };

  const hasSkills = user?.skills && user.skills.trim().length > 0;

  return (
    <div className="app-layout">
      <Sidebar activePage="skillgap" />

      <div className="main-content">
        <header className="main-header">
          <h2>Skill Gap Intelligence</h2>
          <div className="header-actions">
            <div className="header-avatar" id="headerAvatar">
              {user?.full_name?.charAt(0)?.toUpperCase()}
            </div>
          </div>
        </header>

        <div className="page-content content-max-1280">
          {/* Role Selector */}
          <motion.div className="skill-gap-header-epic" initial={{opacity: 0, y: -20}} animate={{opacity: 1, y: 0}}>
            <h3>Target Role Analysis</h3>
            <p>Select your dream job role and we'll analyze the gap between your current skills and what's required.</p>

            <div className="role-selector-wrapper">
              <div className="select-wrapper">
                <select
                  className="epic-input role-select"
                  value={selectedRole}
                  onChange={e => setSelectedRole(e.target.value)}
                >
                  <option value="">Select your target role...</option>
                  {roles.map(role => (
                    <option key={role} value={role}>{role}</option>
                  ))}
                </select>
                <span className="material-symbols-outlined dropdown-icon">expand_more</span>
              </div>
            </div>
          </motion.div>

          {/* No role selected */}
          {!selectedRole && (
            <motion.div className="empty-state-card" initial={{opacity:0}} animate={{opacity:1}}>
              <span className="material-symbols-outlined empty-icon">target</span>
              <h4>Please select a target role to see skill gap</h4>
              <p>Choose your dream job role above and we'll show you exactly what skills you need to develop.</p>
            </motion.div>
          )}

          {/* No skills warning */}
          {selectedRole && !hasSkills && !loading && (
            <motion.div className="warning-card" initial={{opacity:0, y:10}} animate={{opacity:1, y:0}}>
              <span className="material-symbols-outlined">info</span>
              <p>Add skills in your <a href="/profile">Profile</a> to get a personalized analysis.</p>
            </motion.div>
          )}

          {/* Loading */}
          {loading && (
            <div className="loading-container-epic">
              <div className="spinner-epic">
                <span className="material-symbols-outlined spinner-icon-epic">sync</span>
              </div>
              <p>Analyzing skill gap...</p>
            </div>
          )}

          {/* Error */}
          {error && (
            <motion.div initial={{opacity:0, y:-10}} animate={{opacity:1, y:0}} className="toast-epic toast-error">
              <span className="material-symbols-outlined">error</span> {error}
            </motion.div>
          )}

          {/* Results */}
          {analysis && !loading && (
            <motion.div variants={staggerVars} initial="hidden" animate="visible">

              {/* Match percentage ring */}
              <motion.div className="match-summary-card" variants={cardVars}>
                <div className="match-ring-container">
                  <div className="match-ring">
                    <svg viewBox="0 0 120 120">
                      <circle cx="60" cy="60" r="52" className="ring-bg" />
                      <circle cx="60" cy="60" r="52" className="ring-fill"
                        style={{ strokeDasharray: `${analysis.match_percentage * 3.27} 327` }}
                      />
                    </svg>
                    <span className="match-pct">{analysis.match_percentage}%</span>
                  </div>
                  <p className="match-label">Skill Match</p>
                </div>
                <div className="match-stats">
                  <div className="stat-item stat-green">
                    <span className="material-symbols-outlined">check_circle</span>
                    <div>
                      <strong>{analysis.matched_skills.length}</strong>
                      <span>Skills Matched</span>
                    </div>
                  </div>
                  <div className="stat-item stat-red">
                    <span className="material-symbols-outlined">cancel</span>
                    <div>
                      <strong>{analysis.missing_skills.length}</strong>
                      <span>Skills Missing</span>
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Matched Skills */}
              {analysis.matched_skills.length > 0 && (
                <motion.div className="skills-section" variants={cardVars}>
                  <h4><span className="material-symbols-outlined icon-green">verified</span> Your Matched Skills</h4>
                  <div className="skill-tags-display">
                    {analysis.matched_skills.map((skill, i) => (
                      <span key={i} className="skill-badge skill-badge-green">{skill}</span>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Missing Skills */}
              {analysis.missing_skills.length > 0 && (
                <motion.div className="skills-section" variants={cardVars}>
                  <h4><span className="material-symbols-outlined icon-red">pending</span> Skills to Develop</h4>
                  <div className="skill-tags-display">
                    {analysis.missing_skills.map((skill, i) => (
                      <span key={i} className="skill-badge skill-badge-red">{skill}</span>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Learning Path */}
              {analysis.learning_path && analysis.learning_path.length > 0 && (
                <motion.div className="learning-section" variants={cardVars}>
                  <h4><span className="material-symbols-outlined icon-purple">school</span> Recommended Learning Path</h4>
                  <div className="learning-grid">
                    {analysis.learning_path.map((item, i) => (
                      <motion.div className="learning-card" key={i} variants={cardVars} whileHover={{y: -4, scale: 1.01}}>
                        <h5>{item.skill}</h5>
                        <ul>
                          {item.topics.map((topic, j) => (
                            <li key={j}>
                              <span className="material-symbols-outlined">arrow_right</span>
                              {topic}
                            </li>
                          ))}
                        </ul>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Message if any */}
              {analysis.message && (
                <motion.div className="warning-card" variants={cardVars}>
                  <span className="material-symbols-outlined">info</span>
                  <p>{analysis.message}</p>
                </motion.div>
              )}

            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SkillGap;
