import React, { useState, useEffect, useRef } from 'react';
import Sidebar from '../components/Sidebar';
import { getUser, apiGet, apiPost, updateStoredUser, getToken } from '../utils/api';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import './Profile.css';

const API_BASE = 'http://localhost:5000';

const Profile = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [userState, setUserState] = useState(null);
  const [formData, setFormData] = useState({
    degree: '', branch: '', gpa: '', specialization: '',
    experience: '', certifications: '', skills: '', target_role: ''
  });
  const [availableRoles, setAvailableRoles] = useState([]);

  const [skillsList, setSkillsList] = useState([]);
  const [skillInput, setSkillInput] = useState('');

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    let u = getUser();
    if (!u) {
      navigate('/login');
      return;
    }

    const loadProfile = async () => {
      try {
        const res = await apiGet('/profile/me');
        if (res?.user) {
          u = res.user;
          localStorage.setItem('edu2job_user', JSON.stringify(u));
        }
      } catch (err) {}
      
      setUserState(u);
      setFormData({
        degree: u.degree || '',
        branch: u.branch || '',
        gpa: u.gpa || '',
        specialization: u.specialization || '',
        experience: u.experience || '',
        certifications: u.certifications || '',
        target_role: u.target_role || '',
      });
      if (u.skills) {
        const parsedSkills = u.skills.split(',').map(s => s.trim()).filter(Boolean);
        setSkillsList(parsedSkills);
      }

      // Load available roles for target role dropdown
      try {
        const rolesRes = await apiGet('/skillgap/roles');
        if (rolesRes.roles) setAvailableRoles(rolesRes.roles);
      } catch (e) { /* silent */ }
    };

    loadProfile();
  }, [navigate]);

  const showToast = (msg, type = 'success') => {
    if (type === 'error') setError(msg);
    else setSuccess(msg);
    setTimeout(() => { setError(''); setSuccess(''); }, 3200);
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.id]: e.target.value });
  };

  const handleSkillKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const val = skillInput.trim();
      if (val && !skillsList.includes(val)) {
        setSkillsList([...skillsList, val]);
      }
      setSkillInput('');
    }
  };

  const removeSkill = (name) => {
    setSkillsList(skillsList.filter(s => s !== name));
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    const data = {
      ...formData,
      gpa: parseFloat(formData.gpa) || 0,
      experience: parseInt(formData.experience, 10) || 0,
      skills: skillsList.join(','),
    };
    try {
      const res = await apiPost('/profile/update', data);
      if (res.message) {
        updateStoredUser(data);
        showToast('Matrix Synchronized!', 'success');
      } else {
        showToast(res.error || 'Sync failed', 'error');
      }
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleZoneClick = () => fileInputRef.current.click();
  const handleDragOver = (e) => e.preventDefault();
  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files.length) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };
  const handleFileChange = (e) => {
    if (e.target.files.length) {
      setSelectedFile(e.target.files[0]);
    }
  };
  const removeSelectedFile = () => setSelectedFile(null);

  const handleFileUpload = async () => {
    if (!selectedFile) return;
    const data = new FormData();
    data.append('resume', selectedFile);

    setUploading(true);
    try {
      const token = getToken();
      const res = await fetch(API_BASE + '/resume/upload', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: data,
      });
      const parsedRes = await res.json();
      setUploading(false);

      if (res.ok) {
        showToast('Neural extraction complete!', 'success');
        if (parsedRes.parsed) {
          const p = parsedRes.parsed;
          setFormData(prev => ({
            ...prev,
            degree: p.degree || prev.degree,
            branch: p.branch || prev.branch,
            gpa: p.gpa > 0 ? p.gpa : prev.gpa,
            experience: p.experience > 0 ? p.experience : prev.experience,
            certifications: p.certifications || prev.certifications,
          }));
          if (p.skills && p.skills.length) {
            setSkillsList(Array.from(new Set([...skillsList, ...p.skills])));
          }

          updateStoredUser({
            degree: p.degree || '',
            gpa: p.gpa || 0,
            experience: p.experience || 0,
            certifications: p.certifications || '',
            skills: (p.skills || []).join(','),
          });
          
          showToast(`Nodes extracted: ${p.skills ? p.skills.length : 0}`, 'success');
        }
      } else {
        showToast(parsedRes.error || 'Extraction failed', 'error');
      }
    } catch (err) {
      setUploading(false);
      showToast(err.message || 'Upload error', 'error');
    }
    removeSelectedFile();
  };

  const staggerVars = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };
  const cardVars = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 200 } }
  };

  return (
    <div className="app-layout">
      <Sidebar activePage="profile" />

      <div className="main-content">
        <header className="main-header">
          <h2>Identity Matrix</h2>
          <div className="header-actions">
            <button className="notification-btn dark-btn">
              <span className="material-symbols-outlined">notifications</span>
              <span className="notification-dot"></span>
            </button>
            <div className="header-avatar" id="headerAvatar"></div>
          </div>
        </header>

        <div className="page-content content-max-1400">
          {(error || success) && (
             <motion.div initial={{opacity:0, y:-10}} animate={{opacity:1, y:0}} className={`toast-epic toast-${error ? 'error' : 'success'}`}>
               <span className="material-symbols-outlined">{error ? 'error' : 'check_circle'}</span>
               {error || success}
             </motion.div>
          )}

          <motion.div className="content-header-epic" initial={{opacity:0, y:-20}} animate={{opacity:1, y:0}}>
            <h3 className="content-title-epic">Configure Your Identity</h3>
            <p className="content-desc-epic">Feed your raw data into the system or let our AI instantly extract your career matrix from your uploaded resume. Accuracy yields precision.</p>
          </motion.div>

          <motion.div className="profile-grid-epic" variants={staggerVars} initial="hidden" animate="visible">
            
            {/* Form Card */}
            <motion.div className="profile-card-epic" variants={cardVars}>
              <div className="card-glow blue-glow-soft"></div>
              <h4>
                <div className="icon-wrap blue-wrap"><span className="material-symbols-outlined">account_circle</span></div>
                Base Parameters
              </h4>
              
              <form onSubmit={handleSaveProfile} noValidate className="epic-form">
                <div className="form-row form-row-spaced">
                  <div className="form-group">
                    <label htmlFor="degree">System Degree</label>
                    <div className="select-wrapper">
                      <select id="degree" value={formData.degree} onChange={handleChange} className="epic-input">
                        <option value="">Select Degree</option>
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
                  <div className="form-group">
                    <label htmlFor="branch">Core Branch</label>
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

                <div className="form-row form-row-spaced">
                  <div className="form-group">
                    <label htmlFor="gpa">Performance Index (GPA)</label>
                    <input type="number" id="gpa" value={formData.gpa} onChange={handleChange} placeholder="e.g. 3.8" step="0.1" className="epic-input" />
                  </div>
                  <div className="form-group">
                    <label htmlFor="specialization">Specialization <span className="label-optional">(optional)</span></label>
                    <input type="text" id="specialization" value={formData.specialization} onChange={handleChange} placeholder="e.g. Neural Networks" className="epic-input" />
                  </div>
                </div>

                <div className="form-group">
                  <label>Skill Nodes</label>
                  <div className="skill-tags-wrapper-epic">
                    {skillsList.map((skill, index) => (
                      <motion.span key={index} className="skill-tag-epic" initial={{scale:0.8, opacity:0}} animate={{scale:1, opacity:1}}>
                        {skill} <span className="material-symbols-outlined remove" onClick={() => removeSkill(skill)}>close</span>
                      </motion.span>
                    ))}
                    <input type="text" value={skillInput} onChange={(e) => setSkillInput(e.target.value)} onKeyDown={handleSkillKeyDown} placeholder="Initialize node..." className="epic-node-input" />
                  </div>
                </div>

                <div className="form-row form-row-spaced">
                  <div className="form-group">
                    <label htmlFor="experience">Cycles (Years Experience)</label>
                    <input type="number" id="experience" value={formData.experience} onChange={handleChange} placeholder="2" min="0" className="epic-input" />
                  </div>
                  <div className="form-group">
                    <label htmlFor="certifications">Active Certifications</label>
                    <input type="text" id="certifications" value={formData.certifications} onChange={handleChange} placeholder="AWS Cloud, PMP..." className="epic-input" />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="target_role">Dream Job Role <span className="label-optional">(for Skill Gap)</span></label>
                  <div className="select-wrapper">
                    <select id="target_role" value={formData.target_role} onChange={handleChange} className="epic-input">
                      <option value="">Select Target Role</option>
                      {availableRoles.map(role => (
                        <option key={role} value={role}>{role}</option>
                      ))}
                    </select>
                    <span className="material-symbols-outlined dropdown-icon">expand_more</span>
                  </div>
                </div>

                <button type="submit" className="btn btn-primary btn-epic">
                  <span className="material-symbols-outlined">sync</span> Synchronize Matrix
                </button>
              </form>
            </motion.div>

            {/* Resume Card */}
            <motion.div className="profile-card-epic" variants={cardVars}>
              <div className="card-glow purple-glow-soft"></div>
              <h4>
                <div className="icon-wrap purple-wrap"><span className="material-symbols-outlined">memory</span></div>
                Auto-Extraction
              </h4>
              <p className="upload-desc-epic">
                Upload your raw resume file and let our AI parser instantly build your identity matrix.
              </p>

              <div className="upload-zone-epic" onClick={handleZoneClick} onDragOver={handleDragOver} onDrop={handleDrop}>
                <div className="upload-icon-circle-epic">
                  <span className="material-symbols-outlined upload-icon-pulse">cloud_upload</span>
                </div>
                <h5>Initiate Uplink</h5>
                <p>PDF, DOCX (Max 5MB)</p>
                <input type="file" ref={fileInputRef} onChange={handleFileChange} accept=".pdf,.doc,.docx,.txt" className="hidden-input" />
              </div>

              {selectedFile && (
                <motion.div initial={{opacity:0, y:10}} animate={{opacity:1, y:0}}>
                  <div className="file-card-epic">
                    <div className="file-info">
                      <div className="file-icon-epic"><span className="material-symbols-outlined">description</span></div>
                      <div>
                        <p className="file-name-epic">{selectedFile.name}</p>
                        <p className="file-meta-epic">{(selectedFile.size / (1024 * 1024)).toFixed(1)} MB</p>
                      </div>
                    </div>
                    <button className="file-delete-epic" onClick={removeSelectedFile}>
                      <span className="material-symbols-outlined">delete</span>
                    </button>
                  </div>

                  <button type="button" className="btn btn-epic-glow btn-full" onClick={handleFileUpload} disabled={uploading}>
                    <span className="material-symbols-outlined">{uploading ? 'hourglass_empty' : 'rocket_launch'}</span>
                    {uploading ? 'Running Parse Algorithm...' : 'Execute Extraction'}
                  </button>
                </motion.div>
              )}
            </motion.div>

          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
