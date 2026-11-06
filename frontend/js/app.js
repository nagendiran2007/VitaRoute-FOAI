async function fetchJson(url, options = {}) {
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
  const text = await response.text();
  try { return JSON.parse(text); } catch (error) { return { message: text }; }
}

function showMessage(text, isError = false) {
  const box = document.getElementById('messageBox');
  if (box) {
    box.style.display = 'block';
    box.textContent = text;
    box.style.color = isError ? '#d68a7d' : '#8bdcc0';
  }
  showToast(text, isError);
}

function showToast(text, isError = false) {
  const toast = document.createElement('div');
  toast.className = `toast-message${isError ? ' error' : ''}`;
  toast.setAttribute('role', isError ? 'alert' : 'status');
  toast.textContent = text;
  document.body.appendChild(toast);
  window.setTimeout(() => toast.remove(), 3800);
}

async function bootstrapSession() {
  const session = await fetchJson('/api/session');
  const user = session.user;
  if (!user) {
    if (window.location.pathname !== '/login' && window.location.pathname !== '/loading' && window.location.pathname !== '/register-hospital') {
      window.location.href = '/login';
    }
    return null;
  }
  return user;
}

async function populateOverview() {
  const user = await bootstrapSession();
  if (!user) return;
  const endpoint = user.role === 'admin' ? '/api/admin/overview' : '/api/hospital/overview';
  const data = await fetchJson(endpoint);
  const cards = document.querySelectorAll('[data-stat]');
  cards.forEach((card) => {
    const key = card.dataset.stat;
    if (data[key] !== undefined) card.textContent = data[key];
  });
}

async function populateTable(selector, endpoint, formatter) {
  const tableBody = document.querySelector(selector);
  if (!tableBody) return;
  const data = await fetchJson(endpoint);
  tableBody.innerHTML = '';
  data.forEach((row) => {
    const tr = document.createElement('tr');
    tr.innerHTML = formatter(row);
    tableBody.appendChild(tr);
  });
}

function attachLogoutHandler() {
  const btn = document.getElementById('logoutButton');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    await fetchJson('/api/logout', { method: 'POST' });
    window.location.href = '/login';
  });
}

function attachLoginForm() {
  const form = document.getElementById('loginForm');
  if (!form) return;
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = {
      email: form.email.value.trim(),
      password: form.password.value,
    };
    const result = await fetchJson('/api/login', { method: 'POST', body: JSON.stringify(payload) });
    if (result.success) {
      window.location.href = result.redirect;
    } else {
      showMessage(result.message || 'Login failed.', true);
    }
  });
}

async function checkDatabaseStatus() {
  const status = document.getElementById('databaseStatus');
  const button = document.getElementById('loginButton');
  if (!status || !button) return;
  button.disabled = true;
  try {
    const response = await fetch('/api/database-status', { cache: 'no-store' });
    const result = await response.json();
    status.textContent = result.message || (result.connected ? 'Database connected.' : 'Database unavailable.');
    status.style.color = result.connected ? '#247b5a' : '#a1433b';
    button.disabled = !result.connected;
  } catch (error) {
    status.textContent = 'Could not verify the database connection. Please try again.';
    status.style.color = '#a1433b';
  }
}

function attachHospitalRegistrationForm() {
  const form = document.getElementById('hospitalRegistrationForm');
  if (!form) return;
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(form).entries());
    payload.latitude = Number(payload.latitude || 0);
    payload.longitude = Number(payload.longitude || 0);
    const result = await fetchJson('/api/register-hospital', { method: 'POST', body: JSON.stringify(payload) });
    showMessage(result.message || 'Submitted.', !result.success);
    if (result.success) form.reset();
  });
}

function attachMatchingRun() {
  const button = document.getElementById('runMatchingButton');
  if (!button) return;
  button.addEventListener('click', async () => {
    const result = await fetchJson('/api/matches/run', { method: 'POST' });
    if (result.success) {
      showMessage('Intelligent matching complete.');
      window.location.href = '/matches';
    }
  });
}

function runLoadingTransition() {
  const bar = document.getElementById('loadingBar');
  const percent = document.getElementById('loadingPercent');
  if (!bar || !percent) return;
  let value = 0;
  const interval = setInterval(() => {
    value += 7;
    if (value > 100) value = 100;
    bar.style.width = `${value}%`;
    percent.textContent = `${value}%`;
    if (value >= 100) {
      clearInterval(interval);
      setTimeout(() => {
        window.location.href = '/login';
      }, 500);
    }
  }, 180);
}

function setupNavigation() {
  const path = window.location.pathname.replace(/\/$/, '') || '/';
  document.querySelectorAll('.sidebar .nav-item').forEach((link) => {
    const linkPath = new URL(link.href, window.location.origin).pathname.replace(/\/$/, '');
    link.classList.toggle('active', linkPath === path);
    if (linkPath === path) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });

  const sidebar = document.querySelector('.sidebar');
  const topbar = document.querySelector('.topbar');
  if (!sidebar || !topbar) return;

  const heading = topbar.querySelector(':scope > div:first-child');
  if (heading && !heading.querySelector('.mobile-menu-button')) {
    heading.classList.add('topbar-heading');
    const menuButton = document.createElement('button');
    menuButton.className = 'theme-toggle mobile-menu-button';
    menuButton.type = 'button';
    menuButton.setAttribute('aria-label', 'Open navigation menu');
    menuButton.setAttribute('aria-expanded', 'false');
    menuButton.textContent = '☰';
    heading.prepend(menuButton);
    menuButton.addEventListener('click', () => {
      const isOpen = document.body.classList.toggle('nav-open');
      menuButton.setAttribute('aria-expanded', String(isOpen));
      menuButton.setAttribute('aria-label', isOpen ? 'Close navigation menu' : 'Open navigation menu');
    });
    document.addEventListener('click', (event) => {
      if (!document.body.classList.contains('nav-open')) return;
      if (!sidebar.contains(event.target) && !menuButton.contains(event.target)) {
        document.body.classList.remove('nav-open');
        menuButton.setAttribute('aria-expanded', 'false');
      }
    });
    sidebar.querySelectorAll('.nav-item').forEach((link) => {
      link.addEventListener('click', () => document.body.classList.remove('nav-open'));
    });
  }

  if (!topbar.querySelector('.theme-toggle:not(.mobile-menu-button)')) {
    const themeButton = document.createElement('button');
    themeButton.className = 'theme-toggle';
    themeButton.type = 'button';
    themeButton.setAttribute('aria-label', 'Toggle light theme');
    topbar.appendChild(themeButton);
    const applyTheme = (theme) => {
      document.body.dataset.theme = theme;
      themeButton.textContent = theme === 'light' ? '☾' : '☼';
      themeButton.setAttribute('aria-pressed', String(theme === 'light'));
    };
    applyTheme(localStorage.getItem('vitaroute-theme') || 'dark');
    themeButton.addEventListener('click', () => {
      const theme = document.body.dataset.theme === 'light' ? 'dark' : 'light';
      localStorage.setItem('vitaroute-theme', theme);
      applyTheme(theme);
    });
  }
}

function setupTableInteractions() {
  document.querySelectorAll('.table').forEach((table) => {
    if (table.dataset.interactive === 'true') return;
    table.dataset.interactive = 'true';
    const parent = table.parentElement;
    if (!parent) return;

    const search = document.createElement('input');
    search.className = 'table-search';
    search.type = 'search';
    search.placeholder = 'Search this table...';
    search.setAttribute('aria-label', 'Search table rows');
    parent.insertBefore(search, table);

    const wrapper = document.createElement('div');
    wrapper.className = 'table-wrap';
    table.parentNode.insertBefore(wrapper, table);
    wrapper.appendChild(table);

    search.addEventListener('input', () => {
      const term = search.value.trim().toLocaleLowerCase();
      table.querySelectorAll('tbody tr').forEach((row) => {
        row.hidden = !row.textContent.toLocaleLowerCase().includes(term);
      });
    });

    table.querySelectorAll('thead th').forEach((header, columnIndex) => {
      header.dataset.sortable = 'true';
      header.setAttribute('tabindex', '0');
      header.setAttribute('aria-label', `${header.textContent.trim()}, activate to sort`);
      const sortRows = () => {
        const body = table.tBodies[0];
        if (!body) return;
        const direction = header.dataset.sortDirection === 'asc' ? 'desc' : 'asc';
        header.dataset.sortDirection = direction;
        const rows = [...body.rows];
        rows.sort((a, b) => {
          const first = a.cells[columnIndex]?.textContent.trim() || '';
          const second = b.cells[columnIndex]?.textContent.trim() || '';
          return first.localeCompare(second, undefined, { numeric: true, sensitivity: 'base' }) * (direction === 'asc' ? 1 : -1);
        });
        rows.forEach((row) => body.appendChild(row));
      };
      header.addEventListener('click', sortRows);
      header.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          sortRows();
        }
      });
    });
  });
}

function populateProfile() {
  const profileName = document.querySelector('.signoff [data-profile-name]');
  const profileRole = document.querySelector('.signoff [data-profile-role]');
  fetchJson('/api/session').then(({ user }) => {
    if (!user) return;
    if (profileName) profileName.textContent = user.name || user.username;
    if (profileRole) profileRole.textContent = user.role === 'admin' ? 'System Administrator' : 'Hospital';
  });
}

document.addEventListener('DOMContentLoaded', () => {
  checkDatabaseStatus();
  if (document.getElementById('databaseStatus')) {
    window.setInterval(checkDatabaseStatus, 10000);
  }
  attachLoginForm();
  attachHospitalRegistrationForm();
  attachLogoutHandler();
  setupNavigation();
  setupTableInteractions();
  populateProfile();
  runLoadingTransition();
  if (document.getElementById('overviewStats')) populateOverview();
});
