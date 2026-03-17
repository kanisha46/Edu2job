/* =====================================================
   Edu2Job – script.js
   API helpers, auth, sidebar renderer, toast notifications
   ===================================================== */

const API_BASE = 'http://localhost:5000';

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

async function apiPost(endpoint, data) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(API_BASE + endpoint, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
  return res.json();
}

async function apiGet(endpoint) {
  const token = getToken();
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(API_BASE + endpoint, { headers });
  return res.json();
}

// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------

function getToken() {
  return localStorage.getItem('edu2job_token');
}

function getUser() {
  try {
    return JSON.parse(localStorage.getItem('edu2job_user'));
  } catch {
    return null;
  }
}

function updateStoredUser(updates) {
  const user = getUser();
  if (user) {
    Object.assign(user, updates);
    localStorage.setItem('edu2job_user', JSON.stringify(user));
  }
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = 'login.html';
  }
}

function logout() {
  localStorage.removeItem('edu2job_token');
  localStorage.removeItem('edu2job_user');
  localStorage.removeItem('edu2job_predictions');
  window.location.href = 'login.html';
}

// ---------------------------------------------------------------------------
// Sidebar renderer (supports 'dark' and 'light' variants)
// ---------------------------------------------------------------------------

function renderSidebar(activePage, variant) {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;

  const isDark = variant === 'dark';
  sidebar.className = `sidebar ${isDark ? 'dark' : 'light'}`;

  const user = getUser();
  const initials = user && user.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase()
    : '?';

  const items = [
    { id: 'dashboard',  icon: 'dashboard',    label: 'Dashboard',         href: 'dashboard.html' },
    { id: 'profile',    icon: 'person',       label: 'Profile & Resume',  href: 'profile.html' },
    { id: 'prediction', icon: isDark ? 'psychology' : 'analytics', label: isDark ? 'Job Prediction' : 'Prediction', href: 'prediction.html' },
    { id: 'skillgap',   icon: isDark ? 'map' : 'troubleshoot', label: isDark ? 'Skill Gap Map' : 'Skill Gap', href: 'skillgap.html' },
    { id: 'interview',  icon: 'quiz',         label: 'Interview Prep',    href: 'interview.html' },
  ];

  let html = '';

  // Header
  html += `<div class="sidebar-header">
    <div class="icon-box"><span class="material-symbols-outlined" style="font-size:1.25rem;">school</span></div>
    <div>
      <h1>Edu2Job</h1>
      ${!isDark ? '<p class="sub-text">Career Platform</p>' : ''}
    </div>
  </div>`;

  // Nav
  html += '<nav class="sidebar-nav">';
  items.forEach(item => {
    const active = activePage === item.id ? ' active' : '';
    html += `<a href="${item.href}" class="nav-item${active}">
      <span class="material-symbols-outlined">${item.icon}</span>
      <span>${item.label}</span>
    </a>`;
  });
  html += '</nav>';

  // Footer
  if (isDark) {
    html += `<div class="sidebar-footer">
      <a href="#" class="nav-item" onclick="logout(); return false;">
        <span class="material-symbols-outlined">logout</span>
        <span>Logout</span>
      </a>
    </div>`;
  } else {
    html += `<div class="sidebar-footer">
      <div class="user-card" onclick="logout()">
        <div class="user-avatar">${initials}</div>
        <div style="flex:1; overflow:hidden;">
          <p class="user-name" style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${user ? user.full_name || user.email : 'User'}</p>
          <p class="user-role">${user && user.degree ? user.degree : 'Student'}</p>
        </div>
      </div>
    </div>`;
  }

  sidebar.innerHTML = html;
}

// ---------------------------------------------------------------------------
// Toast notifications
// ---------------------------------------------------------------------------

function showToast(message, type) {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `toast toast-${type || 'success'}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => toast.remove(), 3200);
}
