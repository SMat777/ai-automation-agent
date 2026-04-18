// ═══════════════════════════════════════════════════════════════════════════
// RUN HISTORY SIDEBAR (Fase 1.5 Del B)
//
// Responsibilities:
//   1. Fetch /api/runs on load + on filter change + after every tool run
//   2. Render run cards with status-coloured left edge, tool icon, relative
//      time, duration, and (for errors) a truncated error message
//   3. Click-to-replay: GET /api/runs/{id} → render the full result in
//      the main area using the existing render* functions from app.js
//   4. Mobile drawer: open via topbar menu, close via X or backdrop, and
//      swallow the body scroll while open
//
// Designed per ADR 004: every state (loading, empty, error, hover, active,
// selected) is visibly designed. No default-browser looks anywhere.
// ═══════════════════════════════════════════════════════════════════════════

(function () {
  'use strict';

  // ── State ──────────────────────────────────────────────────────────────
  const state = {
    runs: [],
    total: 0,
    filter: 'all',        // all | errors | today | week
    selectedId: null,     // currently highlighted run card
    isLoading: false,
    isOpen: false,        // mobile drawer open state
  };

  // ── DOM references (bound on DOMContentLoaded) ─────────────────────────
  let els = {};

  function bindDOM() {
    els = {
      sidebar: document.getElementById('sidebar'),
      body: document.getElementById('sidebar-body'),
      loading: document.getElementById('sidebar-loading'),
      total: document.getElementById('sidebar-total'),
      refresh: document.getElementById('sidebar-refresh'),
      filters: document.querySelectorAll('.filter-chip'),
      backdrop: document.getElementById('sidebar-backdrop'),
      menuBtn: document.getElementById('topbar-menu-btn'),
      closeBtn: document.getElementById('sidebar-close-btn'),
    };
  }

  // ── Fetch + render cycle ──────────────────────────────────────────────

  async function fetchRuns() {
    state.isLoading = true;
    renderLoading();

    const params = buildFilterParams(state.filter);
    try {
      const resp = await fetch(`/api/runs?${params}`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      state.runs = data.items;
      state.total = data.total;
      renderRuns();
    } catch (err) {
      console.warn('Failed to load run history:', err);
      renderError();
    } finally {
      state.isLoading = false;
    }
  }

  function buildFilterParams(filter) {
    const p = new URLSearchParams({ limit: '50' });
    switch (filter) {
      case 'errors':
        p.set('status', 'error');
        break;
      case 'today':
        p.set('since', 'today');
        break;
      case 'week':
        p.set('since', 'week');
        break;
      // 'all' → no extra params
    }
    return p.toString();
  }

  // ── Rendering ──────────────────────────────────────────────────────────

  const TOOL_ICONS = {
    analyze: '🔍',
    extract: '📋',
    summarize: '✏️',
    process: '⚡',
    pipeline: '🔄',
    chat: '💬',
  };

  function renderLoading() {
    // Show skeletons for 200ms at least so a fast refresh doesn't flash.
    els.body.innerHTML = `
      <div class="sidebar-loading">
        <div class="skeleton-run"></div>
        <div class="skeleton-run"></div>
        <div class="skeleton-run"></div>
        <div class="skeleton-run"></div>
      </div>
    `;
  }

  function renderError() {
    els.body.innerHTML = `
      <div class="sidebar-empty">
        <div class="sidebar-empty-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M12 8v4m0 4h.01M5.07 19h13.86a2 2 0 001.74-3L13.74 5a2 2 0 00-3.48 0L3.33 16a2 2 0 001.74 3z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="sidebar-empty-title">Couldn't load history</div>
        <div class="sidebar-empty-text">Is the server reachable? Try refreshing.</div>
      </div>
    `;
    els.total.textContent = '—';
  }

  function renderRuns() {
    if (state.runs.length === 0) {
      renderEmpty();
      els.total.textContent = '0 runs';
      return;
    }

    const html = state.runs.map(runCardHTML).join('');
    els.body.innerHTML = html;

    // Wire up click handlers
    els.body.querySelectorAll('.run-card').forEach(card => {
      card.addEventListener('click', () => openRun(Number(card.dataset.runId)));
      card.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openRun(Number(card.dataset.runId));
        }
      });
    });

    els.total.textContent = state.total === 1 ? '1 run' : `${state.total} runs`;
  }

  function renderEmpty() {
    const msg = emptyMessageForFilter(state.filter);
    els.body.innerHTML = `
      <div class="sidebar-empty">
        <div class="sidebar-empty-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M12 8v4l3 2M12 3a9 9 0 100 18 9 9 0 000-18z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="sidebar-empty-title">${msg.title}</div>
        <div class="sidebar-empty-text">${msg.text}</div>
      </div>
    `;
  }

  function emptyMessageForFilter(filter) {
    switch (filter) {
      case 'errors':
        return { title: 'No errors', text: 'Nothing broke recently — everything is green.' };
      case 'today':
        return { title: 'Nothing today', text: 'Try running a tool to see it appear here.' };
      case 'week':
        return { title: 'Nothing this week', text: 'Run a tool to build up your history.' };
      default:
        return { title: 'No runs yet', text: 'Start by picking a demo from the main area.' };
    }
  }

  function runCardHTML(run) {
    const icon = TOOL_ICONS[run.tool_name] || '·';
    const isActive = run.id === state.selectedId;
    const statusClass = run.status === 'success' ? 'status-success' : 'status-error';
    const time = formatRelativeTime(run.created_at);
    const fullTime = new Date(run.created_at).toLocaleString();

    const errorBit = run.error_message
      ? `<span class="run-card-error" title="${escHtml(run.error_message)}">${escHtml(run.error_message)}</span>`
      : '';

    return `
      <button type="button"
              class="run-card ${statusClass}${isActive ? ' active' : ''}"
              data-run-id="${run.id}"
              aria-label="Open ${escHtml(run.tool_name)} run from ${time}">
        <div class="run-card-row">
          <span class="run-card-icon" aria-hidden="true">${icon}</span>
          <span class="run-card-tool">${escHtml(run.tool_name)}</span>
          <span class="run-card-time" title="${escHtml(fullTime)}">${time}</span>
        </div>
        <div class="run-card-meta">
          <span class="run-card-duration">${formatDuration(run.duration_ms)}</span>
          ${errorBit || `<span>·</span><span>${run.status}</span>`}
        </div>
      </button>
    `;
  }

  // ── Opening a run (click → detail → render in main area) ───────────────

  async function openRun(runId) {
    state.selectedId = runId;
    // Immediate visual feedback on the card
    els.body.querySelectorAll('.run-card').forEach(c => c.classList.remove('active'));
    const card = els.body.querySelector(`.run-card[data-run-id="${runId}"]`);
    if (card) card.classList.add('active');

    try {
      const resp = await fetch(`/api/runs/${runId}`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const run = await resp.json();
      renderRunDetail(run);
      closeDrawerIfMobile();
    } catch (err) {
      console.warn('Failed to load run detail:', err);
      window.showToast?.('Couldn\'t load run detail', 'error');
    }
  }

  function renderRunDetail(run) {
    // Switch to the appropriate tab (so the user sees matching UI affordances)
    const tabMap = {
      analyze: 'analyze',
      extract: 'extract',
      summarize: 'summarize',
      process: 'process',
      pipeline: 'pipeline',
      chat: 'chat',
    };
    const toolId = tabMap[run.tool_name] || 'analyze';
    window.switchToTool?.(toolId);

    // Use the matching renderer from app.js if available
    const renderers = {
      analyze: window.renderAnalyze,
      extract: window.renderExtract,
      summarize: window.renderSummarize,
      process: window.renderProcess,
      pipeline: window.renderPipeline,
    };
    const renderer = renderers[run.tool_name];
    const data = run.output_json;

    window.setResultHeader?.(
      `${toTitle(run.tool_name)} — replay`,
      `Run #${run.id} · ${new Date(run.created_at).toLocaleString()}`,
    );

    if (run.status === 'error') {
      window.showResult?.(`
        <div class="error-message">
          <span class="error-icon">⚠️</span>
          ${escHtml(run.error_message || 'Run failed without a message')}
        </div>
      `);
      return;
    }

    if (renderer && data) {
      renderer(data);
    } else if (data) {
      // Fallback: pretty-print JSON for tools without a dedicated renderer.
      window.showResult?.(
        `<pre class="erp-json">${escHtml(JSON.stringify(data, null, 2))}</pre>`
      );
    } else {
      window.showResult?.(
        '<p class="empty-state">No output recorded for this run.</p>'
      );
    }
  }

  // ── Filter chips ───────────────────────────────────────────────────────

  function wireFilters() {
    els.filters.forEach(chip => {
      chip.addEventListener('click', () => {
        const filter = chip.dataset.filter;
        if (filter === state.filter) return;
        state.filter = filter;
        els.filters.forEach(c => c.classList.toggle('active', c === chip));
        fetchRuns();
      });
    });
  }

  // ── Refresh button ─────────────────────────────────────────────────────

  function wireRefresh() {
    els.refresh.addEventListener('click', () => {
      els.refresh.classList.add('spinning');
      setTimeout(() => els.refresh.classList.remove('spinning'), 800);
      fetchRuns();
    });
  }

  // ── Mobile drawer ──────────────────────────────────────────────────────

  function openDrawer() {
    state.isOpen = true;
    els.sidebar.classList.add('open');
    els.backdrop.classList.add('visible');
    els.menuBtn.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
    // Move focus into the drawer for keyboard users
    els.closeBtn.focus();
  }

  function closeDrawer() {
    state.isOpen = false;
    els.sidebar.classList.remove('open');
    els.backdrop.classList.remove('visible');
    els.menuBtn.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }

  function closeDrawerIfMobile() {
    if (window.matchMedia('(max-width: 1023px)').matches && state.isOpen) {
      closeDrawer();
    }
  }

  function wireDrawer() {
    els.menuBtn.addEventListener('click', openDrawer);
    els.closeBtn.addEventListener('click', closeDrawer);
    els.backdrop.addEventListener('click', closeDrawer);
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && state.isOpen) closeDrawer();
    });
  }

  // ── Public API (exposed on window for app.js to call after runs) ───────

  window.runHistory = {
    refresh: fetchRuns,
  };

  // ── Init ───────────────────────────────────────────────────────────────

  function init() {
    bindDOM();
    wireFilters();
    wireRefresh();
    wireDrawer();
    fetchRuns();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // ── Small utilities (local to this module to avoid collisions) ─────────

  function formatRelativeTime(isoString) {
    const now = Date.now();
    const then = new Date(isoString).getTime();
    const diffSec = Math.floor((now - then) / 1000);

    if (diffSec < 60) return 'just now';
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    if (diffSec < 2592000) return `${Math.floor(diffSec / 86400)}d ago`;

    // For older than 30 days, show a short date
    return new Date(isoString).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
    });
  }

  function formatDuration(ms) {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`;
    return `${Math.floor(ms / 60_000)}m ${Math.floor((ms % 60_000) / 1000)}s`;
  }

  function toTitle(s) {
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  function escHtml(s) {
    const div = document.createElement('div');
    div.textContent = String(s ?? '');
    return div.innerHTML;
  }
})();
