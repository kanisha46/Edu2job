import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import { getUser, apiPost } from '../utils/api';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import './Prediction.css';

const roleIcons = {
  'Software Engineer': 'developer_mode',
  'Data Analyst': 'monitoring',
  'Frontend Developer': 'web',
  'Data Scientist': 'psychology',
  'ML Engineer': 'smart_toy',
  'Database Admin': 'storage',
  'DevOps Engineer': 'cloud',
  'Systems Analyst': 'analytics',
  'Backend Developer': 'dns',
  'Full Stack Developer': 'stacks',
  'Cloud Architect': 'cloud_circle',
};
const roleCats = {
  'Software Engineer': 'Tech',
  'Data Analyst': 'Data',
  'Frontend Developer': 'Web',
  'Data Scientist': 'AI / ML',
  'ML Engineer': 'AI / ML',
  'Database Admin': 'Data',
  'DevOps Engineer': 'Cloud',
  'Systems Analyst': 'Tech',
  'Backend Developer': 'Tech',
  'Full Stack Developer': 'Web',
  'Cloud Architect': 'Cloud',
};

const SUGGESTED_SKILLS = [
  'Python', 'Java', 'Javascript', 'React', 'SQL', 'AWS', 'Docker',
  'Machine Learning', 'AutoCAD', 'SolidWorks', 'Ansys', 'Matlab',
  'PLC', 'SCADA', 'Management', 'Marketing', 'Finance', 'Communication',
  'Sales', 'Chemistry', 'Process Engineering', 'HYSYS', 'Thermodynamics'
];

const Prediction = () => {
  const navigate = useNavigate();
  const user = getUser();
  
  const [formData, setFormData] = useState({
    degree: 'B.Tech',
    branch: '',
    gpa: '3.8',
    specialization: '',
    skills: 'Python, React, SQL',
    certifications_count: 0,
    certifications_details: '',
    projects: 0,
    projects_details: '',
    experience: 0,
    internship_details: ''
  });
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const syncFromProfile = () => {
    if (!user) return;
    setFormData(prev => ({
      ...prev,
      certifications_details: user.certifications || prev.certifications_details,
      projects_details: user.projects_details || prev.projects_details,
      internship_details: user.internship_details || prev.internship_details,
      certifications_count: user.certifications_count || prev.certifications_count,
      projects: user.num_projects || prev.projects,
      experience: user.experience || prev.experience
    }));
  };

  useEffect(() => {
    if (!user) {
      navigate('/login');
    } else {
      setFormData(prev => ({
        ...prev,
        degree: user.degree || prev.degree,
        branch: user.branch || prev.branch,
        specialization: user.specialization || prev.specialization,
        gpa: user.gpa > 0 ? user.gpa : prev.gpa,
        skills: user.skills || prev.skills,
        certifications_count: user.certifications_count || 0,
        certifications_details: user.certifications || '',
        projects: user.num_projects || 0,
        projects_details: user.projects_details || '',
        experience: user.experience || 0,
        internship_details: user.internship_details || ''
      }));
    }
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.id]: e.target.value });
  };

  const handleAddSkill = (skill) => {
    const currentSkills = formData.skills ? formData.skills.split(',').map(s => s.trim()) : [];
    if (!currentSkills.includes(skill)) {
      const newSkills = [...currentSkills, skill].filter(s => s).join(', ');
      setFormData({ ...formData, skills: newSkills });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.skills) {
      setError('Neural scan requires skill nodes to proceed.');
      return;
    }
    setError(null);
    setLoading(true);
    setResults(null);

    const payload = {
      ...formData,
      specialization: formData.specialization.trim(),
      skills: formData.skills.trim(),
      gpa: parseFloat(formData.gpa) || 0,
      experience: parseInt(formData.experience) || 0,
      projects: parseInt(formData.projects) || 0,
      certifications_count: parseInt(formData.certifications_count) || 0,
      certifications: "" // Backend expects this key as well
    };

    try {
      const res = await apiPost('/prediction/predict', payload);
      setLoading(false);
      
      if (res.predictions) {
        setResults(res);
        const topPred = res.predictions[0];
        const predEntry = { role: topPred.role, confidence: Math.round(topPred.confidence), date: new Date().toLocaleDateString() };
        const saved = JSON.parse(localStorage.getItem('edu2job_predictions') || '[]');
        saved.push(predEntry);
        localStorage.setItem('edu2job_predictions', JSON.stringify(saved));

        try { await apiPost('/profile/predictions', predEntry); } catch (e) {}
      } else {
        setError(res.error || 'Prediction failed');
      }
    } catch (err) {
      setLoading(false);
      setError(err.message || 'Network anomaly detected.');
    }
  };

  const staggerVars = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.15 } }
  };
  const resultVars = {
    hidden: { opacity: 0, x: -30 },
    visible: { opacity: 1, x: 0, transition: { type: 'spring', stiffness: 200 } }
  };

  return (
    <div className="app-layout">
      <Sidebar activePage="prediction" />

      <div className="main-content">
        <header className="main-header">
          <h2>Career Prediction Engine</h2>
          <div className="header-actions">
            <button className="notification-btn dark-btn">
              <span className="material-symbols-outlined">notifications</span>
            </button>
            <div className="header-avatar" id="headerAvatar"></div>
          </div>
        </header>

        <div className="page-content content-max-1000">
          {error && (
            <motion.div initial={{opacity:0, y:-10}} animate={{opacity:1, y:0}} className="toast-epic toast-error">
               <span className="material-symbols-outlined">error</span> {error}
            </motion.div>
          )}

          <motion.div className="pred-form-card-epic" initial={{opacity:0, scale:0.95}} animate={{opacity:1, scale:1}}>
            <div className="card-glow orange-glow-soft"></div>
            <div className="card-top-header">
              <h3>
                <div className="icon-wrap orange-wrap"><span className="material-symbols-outlined">radar</span></div>
                Prediction Parameters
              </h3>
              <button type="button" className="sync-btn" onClick={syncFromProfile} title="Sync data from your uploaded resume">
                <span className="material-symbols-outlined">sync</span> Sync from AI Profile
              </button>
            </div>
            
            <form onSubmit={handleSubmit} noValidate className="epic-form">
              <div className="form-grid-2 form-grid-spaced">
                <div className="form-group mb-0">
                  <label htmlFor="degree" className="form-label">Degree Sequence</label>
                  <div className="select-wrapper">
                    <select id="degree" value={formData.degree} onChange={handleChange} className="epic-input">
                      <option value="B.Tech">B.Tech</option>
                      <option value="M.Tech">M.Tech</option>
                      <option value="B.Sc">B.Sc</option>
                      <option value="M.Sc">M.Sc</option>
                      <option value="BCA">BCA</option>
                      <option value="MCA">MCA</option>
                      <option value="B.E">B.E</option>
                      <option value="MBA">MBA</option>
                    </select>
                    <span className="material-symbols-outlined dropdown-icon">expand_more</span>
                  </div>
                </div>
                <div className="form-group mb-0">
                  <label htmlFor="branch" className="form-label">Core Branch</label>
                  <div className="select-wrapper">
                    <select id="branch" value={formData.branch} onChange={handleChange} className="epic-input">
                      <option value="">Select Branch</option>
                      <option value="Computer Science">Computer Science</option>
                      <option value="IT">Information Technology</option>
                      <option value="ECE">Electronics & Communication</option>
                      <option value="EE">Electrical Engineering</option>
                      <option value="ME">Mechanical Engineering</option>
                      <option value="Civil">Civil Engineering</option>
                      <option value="AI/ML">AI / ML</option>
                      <option value="Data Science">Data Science</option>
                    </select>
                    <span className="material-symbols-outlined dropdown-icon">expand_more</span>
                  </div>
                </div>
              </div>
              <div className="form-grid-2 form-grid-spaced">
                <div className="form-group mb-0">
                  <label htmlFor="gpa" className="form-label">Performance (GPA)</label>
                  <input type="number" id="gpa" value={formData.gpa} onChange={handleChange} placeholder="e.g. 3.8" step="0.1" className="epic-input" />
                </div>
                <div className="form-group mb-0">
                  <label htmlFor="specialization" className="form-label">Specialization <span className="label-optional">(optional)</span></label>
                  <input type="text" id="specialization" value={formData.specialization} onChange={handleChange} placeholder="e.g. Cloud Computing" className="epic-input" />
                </div>
              </div>

              <div className="form-grid-3 form-grid-spaced">
                <div className="form-group mb-0">
                  <label htmlFor="certifications_count" className="form-label">Certifications</label>
                  <input type="number" id="certifications_count" value={formData.certifications_count} onChange={handleChange} placeholder="0" className="epic-input" />
                </div>
                <div className="form-group mb-0">
                  <label htmlFor="projects" className="form-label">Projects</label>
                  <input type="number" id="projects" value={formData.projects} onChange={handleChange} placeholder="0" className="epic-input" />
                </div>
                <div className="form-group mb-0">
                  <label htmlFor="experience" className="form-label">Internships</label>
                  <input type="number" id="experience" value={formData.experience} onChange={handleChange} placeholder="0" className="epic-input" />
                </div>
              </div>

              <div className="detailed-parameters">
                <div className="form-group">
                  <label htmlFor="certifications_details" className="form-label">Certification Courses (Optional)</label>
                  <textarea id="certifications_details" value={formData.certifications_details} onChange={handleChange} placeholder="e.g. AWS Certified Solutions Architect, Google Data Analytics..." className="epic-input epic-textarea" rows="2"></textarea>
                </div>
                <div className="form-group">
                  <label htmlFor="projects_details" className="form-label">Project Technologies (Optional)</label>
                  <textarea id="projects_details" value={formData.projects_details} onChange={handleChange} placeholder="e.g. Python (Django), React (Redux), Java (Spring Boot)..." className="epic-input epic-textarea" rows="2"></textarea>
                </div>
                <div className="form-group">
                  <label htmlFor="internship_details" className="form-label">Internship Domains (Optional)</label>
                  <textarea id="internship_details" value={formData.internship_details} onChange={handleChange} placeholder="e.g. Web Development, Data Science, Cybersecurity..." className="epic-input epic-textarea" rows="2"></textarea>
                </div>
              </div>
              <div className="form-group mb-0">
                <label htmlFor="skills" className="form-label">Skill Matrix (Comma separated)</label>
                <input type="text" id="skills" value={formData.skills} onChange={handleChange} placeholder="Python, React, SQL..." className="epic-input" />
                <div className="suggested-skills">
                  {SUGGESTED_SKILLS.map(skill => (
                    <button 
                      key={skill} 
                      type="button" 
                      className={`skill-tag ${formData.skills.includes(skill) ? 'active' : ''}`}
                      onClick={() => handleAddSkill(skill)}
                    >
                      {skill}
                    </button>
                  ))}
                </div>
              </div>
              <button type="submit" className="btn btn-epic-primary btn-full" disabled={loading}>
                {loading ? (
                  <><span className="material-symbols-outlined spinner-icon">sync</span> Computing Trajectories...</>
                ) : (
                  <><span className="material-symbols-outlined">explore</span> Predict Top Roles</>
                )}
              </button>
            </form>
          </motion.div>

          {results && (
            <motion.div className="results-section-epic" variants={staggerVars} initial="hidden" animate="visible">
              <h4 className="results-title-epic">Predicted Trajectories</h4>
              <div>
                {results.predictions.map((p, i) => {
                  const icon = roleIcons[p.role] || 'work';
                  const cat = roleCats[p.role] || 'General';
                  const pct = Math.round(p.confidence);
                  const breakdown = p.education_score !== undefined
                    ? `Edu: ${Math.round(p.education_score)}% · Skills: ${Math.round(p.skills_score)}% · Res: ${Math.round(p.resume_score)}% · Cert: ${Math.round(p.certifications_score)}%`
                    : '';

                  return (
                    <motion.div className="result-card-epic" key={i} variants={resultVars} whileHover={{scale: 1.01}}>
                      <div className="result-card-inner-epic">
                        <div className="result-role-info-epic">
                          <div className="result-role-icon-epic"><span className="material-symbols-outlined">{icon}</span></div>
                          <div>
                            <div className="result-role-name-epic">{p.role}</div>
                            <div className="result-role-cat-epic">{cat}</div>
                          </div>
                        </div>
                        <div className="result-bar-container-epic">
                          <div className="result-bar-epic">
                            <div className="result-bar-fill-epic" style={{ width: `${pct}%` }}></div>
                          </div>
                          <span className="result-percent-epic">{pct}%</span>
                        </div>
                      </div>
                      {breakdown && <div className="result-breakdown-epic">{breakdown}</div>}
                      {p.explanations?.length > 0 && (
                        <div className="result-explanations-epic">
                          {p.explanations.map((exp, j) => (
                            <div key={j} className="explanation-item-epic"><span className="material-symbols-outlined">check</span> {exp}</div>
                          ))}
                        </div>
                      )}
                    </motion.div>
                  );
                })}
              </div>

              {results.explanation?.length > 0 && (
                <motion.div className="explanation-card-epic" variants={resultVars}>
                  <h3><span className="material-symbols-outlined icon-purple">psychology</span> AI Telemetry Analysis</h3>
                  <ul className="explanation-list-epic">
                    {results.explanation.map((exp, i) => <li key={i}>{exp}</li>)}
                  </ul>
                </motion.div>
              )}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Prediction;
