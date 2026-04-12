/* app.js – Main application: init, tab routing, re-render scheduling */

let _activeTab       = 'current';
let _rerenderTimer   = null;
let _rerenderTarget  = null;  // null = all tabs, 'savings' = only savings

/* ── Initialization ──────────────────────────────────────────────────────── */
async function init() {
  /* Set today's date in header */
  document.getElementById('today-line').textContent =
    'Today: ' + new Date().toLocaleDateString('en-US', { weekday:'long', month:'long', day:'numeric', year:'numeric' });

  /* Load demo data (graceful fallback) */
  await loadDemoData();

  /* Sidebar toggle */
  document.getElementById('sidebar-close').addEventListener('click', () => {
    document.getElementById('sidebar').classList.add('collapsed');
  });
  document.getElementById('sidebar-open').addEventListener('click', () => {
    document.getElementById('sidebar').classList.remove('collapsed');
  });

  /* Tab navigation */
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => _switchTab(btn.dataset.tab));
  });

  /* First render */
  renderSidebar();
  _renderActiveTab();
}

/* ── Tab switching ───────────────────────────────────────────────────────── */
function _switchTab(tabId) {
  if (_activeTab === tabId) return;
  _activeTab = tabId;

  document.querySelectorAll('.tab-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.tab === tabId),
  );
  document.querySelectorAll('.tab-panel').forEach(p =>
    p.classList.toggle('active', p.id === 'panel-' + tabId),
  );

  _renderActiveTab();
}

/* ── Render the active tab ───────────────────────────────────────────────── */
function _renderActiveTab() {
  /* Always (re)compute current month first — its EOM projection feeds Tab 2 */
  renderTabCurrent();

  switch (_activeTab) {
    case 'current': /* already rendered above */ break;
    case 'next':    renderTabNext();    break;
    case 'savings': renderTabSavings(); break;
  }
}

/* ── Debounced re-render ─────────────────────────────────────────────────── */
/**
 * Schedule a re-render.
 * @param {string|null} target  'savings' to only re-render savings sub-tab,
 *                              null/undefined to re-render active tab.
 */
function scheduleRerender(target) {
  if (target === 'savings' && _activeTab === 'savings') {
    _rerenderTarget = 'savings';
  } else {
    _rerenderTarget = null;
  }

  clearTimeout(_rerenderTimer);
  _rerenderTimer = setTimeout(() => {
    if (_rerenderTarget === 'savings') {
      renderTabCurrent();      // keep EOM projection up-to-date
      renderTabSavings();
    } else {
      _renderActiveTab();
    }
    _rerenderTarget = null;
  }, 120);
}

/* ── Kick off ────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', init);
