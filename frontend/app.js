// ── Navigation ──────────────────────────────────────────────────────────────

let currentView = 'dashboard';
let currentScenario = null;

function navigateTo(view, options = {}) {
  // Hide all views
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));

  // Show target view
  const target = document.getElementById(`view-${view}`);
  if (target) target.classList.add('active');

  // Update nav
  document.querySelectorAll('.nav-item').forEach(item => {
    const itemView = item.dataset.view;
    const itemScenario = item.dataset.scenario;
    if (view === 'scenario' && itemScenario === options.scenario) {
      item.classList.add('active');
    } else if (itemView === view && view !== 'scenario') {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // Update topbar
  const viewName = document.getElementById('topbar-view-name');
  if (viewName) viewName.textContent = target?.querySelector('h1')?.textContent || view;

  currentView = view;

  // Close mobile nav
  document.getElementById('nav-sidebar')?.classList.remove('open');
  document.getElementById('nav-backdrop')?.classList.remove('active');

  // View-specific init
  if (view === 'dashboard') loadDashboard();
  if (view === 'knowledge') loadKnowledgeBase();
  if (view === 'workflows') loadWorkflows();
  if (view === 'scenario' && options.scenario) loadScenario(options.scenario);

  // Re-init Lucide icons for new view
  if (window.lucide) lucide.createIcons();
}

// Nav item clicks
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', () => {
    const view = item.dataset.view;
    const scenario = item.dataset.scenario;
    if (view === 'scenario' && scenario) {
      navigateTo('scenario', { scenario });
    } else {
      navigateTo(view);
    }
  });
});

// Mobile nav toggle
document.getElementById('topbar-menu-btn')?.addEventListener('click', () => {
  document.getElementById('nav-sidebar')?.classList.toggle('open');
  document.getElementById('nav-backdrop')?.classList.toggle('active');
});
document.getElementById('nav-backdrop')?.addEventListener('click', () => {
  document.getElementById('nav-sidebar')?.classList.remove('open');
  document.getElementById('nav-backdrop')?.classList.remove('active');
});

// ── Toast ────────────────────────────────────────────────────────────────────

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// ── API Health Check ─────────────────────────────────────────────────────────

async function checkHealth() {
  const dot = document.getElementById('api-status-dot');
  const text = document.getElementById('api-status-text');
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    dot.className = 'status-dot ok';
    text.textContent = data.api_key_configured ? 'Live Mode' : 'Demo Mode';
  } catch {
    dot.className = 'status-dot err';
    text.textContent = 'Offline';
  }
}

// ── Dashboard ────────────────────────────────────────────────────────────────

let runsChart = null;
let toolsChart = null;

async function loadDashboard() {
  // Load stats
  try {
    const res = await fetch('/api/stats');
    const stats = await res.json();

    document.getElementById('kpi-runs-today').textContent = stats.runs_today || 0;
    document.getElementById('kpi-avg-latency').textContent = `${stats.avg_duration_ms || 0}ms`;
    document.getElementById('kpi-total-cost').textContent = stats.total_cost_usd > 0 ? `$${stats.total_cost_usd.toFixed(4)}` : '$0.00';

    renderRunsChart(stats.runs_by_day || []);
    renderToolsChart(stats.runs_by_tool || {});
  } catch { /* stats API might not have data yet */ }

  // Load documents count
  try {
    const res = await fetch('/api/knowledge');
    const data = await res.json();
    document.getElementById('kpi-documents').textContent = data.count || 0;
  } catch {
    document.getElementById('kpi-documents').textContent = '0';
  }

  // Load scenario cards
  loadScenarioCards();
}

function renderRunsChart(data) {
  const ctx = document.getElementById('chart-runs')?.getContext('2d');
  if (!ctx) return;

  if (runsChart) runsChart.destroy();

  const labels = data.map(d => d.date?.slice(5) || '');
  const values = data.map(d => d.count || 0);

  // Fill empty days
  if (labels.length === 0) {
    for (let i = 6; i >= 0; i--) {
      const d = new Date(); d.setDate(d.getDate() - i);
      labels.push(`${d.getMonth()+1}/${d.getDate()}`);
      values.push(0);
    }
  }

  runsChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Runs',
        data: values,
        borderColor: '#6c7fd8',
        backgroundColor: 'rgba(108,127,216,0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 3,
        pointBackgroundColor: '#6c7fd8',
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { color: '#6b7190', stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.04)' } },
        x: { ticks: { color: '#6b7190' }, grid: { display: false } },
      },
    },
  });
}

function renderToolsChart(data) {
  const ctx = document.getElementById('chart-tools')?.getContext('2d');
  if (!ctx) return;

  if (toolsChart) toolsChart.destroy();

  const labels = Object.keys(data);
  const values = Object.values(data);

  if (labels.length === 0) {
    labels.push('No data');
    values.push(0);
  }

  const colors = ['#6c7fd8', '#4caf7d', '#d4a038', '#d45858', '#8194e8', '#7dd4af', '#d8c06c', '#d47070'];

  toolsChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: colors.slice(0, labels.length), borderWidth: 0 }],
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'right', labels: { color: '#9399b0', boxWidth: 12, padding: 8, font: { size: 11 } } } },
    },
  });
}

async function loadScenarioCards() {
  const grid = document.getElementById('scenario-grid');
  if (!grid) return;

  try {
    const res = await fetch('/api/scenarios');
    const data = await res.json();
    const scenarios = data.scenarios || [];

    grid.innerHTML = scenarios.map(s => `
      <button class="scenario-card" onclick="navigateTo('scenario', {scenario: '${s.id}'})" type="button">
        <div class="scenario-icon"><i data-lucide="${s.icon}"></i></div>
        <div>
          <strong>${s.name}</strong>
          <span>${s.description}</span>
        </div>
      </button>
    `).join('');

    if (window.lucide) lucide.createIcons();
  } catch {
    grid.innerHTML = '<p style="color:var(--text-3)">Could not load scenarios</p>';
  }
}

// ── Scenarios ────────────────────────────────────────────────────────────────

async function loadScenario(scenarioId) {
  try {
    const res = await fetch(`/api/scenarios/${scenarioId}`);
    const scenario = await res.json();
    currentScenario = scenario;

    document.getElementById('scenario-title').textContent = scenario.name;
    document.getElementById('scenario-badge').textContent = scenario.industry;
    document.getElementById('scenario-description').textContent = scenario.description;

    // Suggested prompts
    const promptsEl = document.getElementById('suggested-prompts');
    if (promptsEl && scenario.suggested_prompts) {
      promptsEl.innerHTML = scenario.suggested_prompts.map(p =>
        `<button class="suggestion-btn" onclick="sendScenarioPrompt(this)" type="button">${p}</button>`
      ).join('');
    }

    // Reset output
    document.getElementById('scenario-output').innerHTML = `
      <div class="empty-state">
        <i data-lucide="bot" class="empty-icon"></i>
        <p>Run the agent to see results here</p>
        <div class="suggested-prompts" id="suggested-prompts">
          ${(scenario.suggested_prompts || []).map(p =>
            `<button class="suggestion-btn" onclick="sendScenarioPrompt(this)" type="button">${p}</button>`
          ).join('')}
        </div>
      </div>`;

    document.getElementById('scenario-text').value = '';

    if (window.lucide) lucide.createIcons();
  } catch (e) {
    showToast('Failed to load scenario', 'error');
  }
}

function loadScenarioDemo() {
  if (currentScenario?.demo_input) {
    document.getElementById('scenario-text').value = currentScenario.demo_input;
    showToast('Demo data loaded', 'info');
  }
}

function sendScenarioPrompt(btn) {
  document.getElementById('scenario-text').value = btn.textContent;
  runScenario();
}

async function runScenario() {
  const text = document.getElementById('scenario-text').value.trim();
  if (!text) { showToast('Enter text or load demo data', 'error'); return; }
  if (!currentScenario?.id) { showToast('Select a scenario first', 'error'); return; }

  const output = document.getElementById('scenario-output');
  output.innerHTML = '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>';

  const btn = document.getElementById('btn-scenario-run');
  if (btn) btn.disabled = true;

  try {
    const res = await fetch(`/api/scenarios/${currentScenario.id}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input_text: text }),
    });

    const data = await res.json();

    if (!res.ok) {
      output.innerHTML = `<div class="chat-msg assistant" style="border-left: 3px solid var(--red)">Error: ${escapeHtml(data.detail || 'Scenario run failed')}</div>`;
      return;
    }

    const payload = data.data || data;
    if (window.renderScenarioResult) {
      output.innerHTML = renderScenarioResult(payload);
    } else {
      output.innerHTML = `<pre>${escapeHtml(JSON.stringify(payload, null, 2))}</pre>`;
    }

    showToast('Scenario run complete', 'success');
    if (window.lucide) lucide.createIcons();
  } catch (e) {
    output.innerHTML = `<div class="chat-msg assistant" style="border-left: 3px solid var(--red)">Error: ${escapeHtml(e.message)}</div>`;
    showToast('Scenario run failed', 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ── Upload ───────────────────────────────────────────────────────────────────

const uploadZone = document.getElementById('upload-zone');
const uploadInput = document.getElementById('upload-input');

if (uploadZone) {
  uploadZone.addEventListener('click', () => uploadInput?.click());
  uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
  uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
  uploadZone.addEventListener('drop', e => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
  });
}
uploadInput?.addEventListener('change', () => { if (uploadInput.files.length) uploadFile(uploadInput.files[0]); });

async function uploadFile(file) {
  const progress = document.getElementById('upload-progress');
  const fill = document.getElementById('progress-fill');
  const text = document.getElementById('progress-text');
  const result = document.getElementById('upload-result');

  progress.classList.remove('hidden');
  fill.style.width = '30%';
  text.textContent = `Uploading ${file.name}...`;

  try {
    const formData = new FormData();
    formData.append('file', file);

    fill.style.width = '60%';
    text.textContent = 'Processing and embedding...';

    const res = await fetch('/api/upload', { method: 'POST', body: formData });
    const data = await res.json();

    fill.style.width = '100%';

    if (res.ok) {
      text.textContent = 'Done!';
      result.innerHTML = `<div style="color:var(--green)">✓ <strong>${data.filename}</strong> ingested — ${data.chunk_count || 0} chunks stored in knowledge base</div>`;
      showToast(`${data.filename} uploaded successfully`, 'success');
    } else {
      text.textContent = 'Failed';
      result.innerHTML = `<div style="color:var(--red)">✗ ${data.detail || 'Upload failed'}</div>`;
      showToast(data.detail || 'Upload failed', 'error');
    }
  } catch (e) {
    fill.style.width = '0%';
    text.textContent = 'Error';
    showToast(`Upload error: ${e.message}`, 'error');
  }

  setTimeout(() => { progress.classList.add('hidden'); fill.style.width = '0%'; }, 3000);
}

// ── Knowledge Base ───────────────────────────────────────────────────────────

async function loadKnowledgeBase() {
  const list = document.getElementById('knowledge-list');
  if (!list) return;

  try {
    const res = await fetch('/api/knowledge');
    const data = await res.json();
    const docs = data.documents || [];

    if (docs.length === 0) {
      list.innerHTML = `
        <div class="empty-state">
          <i data-lucide="folder-open" class="empty-icon"></i>
          <p>No documents uploaded yet</p>
          <button class="btn-secondary" onclick="navigateTo('upload')" type="button">
            <i data-lucide="upload"></i> Upload your first document
          </button>
        </div>`;
    } else {
      list.innerHTML = docs.map(d => `
        <div class="doc-card">
          <div class="doc-icon"><i data-lucide="${getFileIcon(d.file_type)}"></i></div>
          <div class="doc-info">
            <div class="doc-name">${d.filename || d.doc_id}</div>
            <div class="doc-meta">${d.file_type || 'unknown'} · ${d.chunk_count || '?'} chunks · ${formatDate(d.created_at)}</div>
          </div>
          <div class="doc-actions">
            <button class="doc-delete-btn" onclick="deleteDocument('${d.doc_id}')" title="Delete" type="button">
              <i data-lucide="trash-2"></i>
            </button>
          </div>
        </div>
      `).join('');
    }

    if (window.lucide) lucide.createIcons();
  } catch {
    list.innerHTML = '<p style="color:var(--text-3);text-align:center;padding:2rem">Could not load knowledge base</p>';
  }
}

function getFileIcon(type) {
  const icons = { pdf: 'file-text', docx: 'file-text', eml: 'mail', txt: 'file', md: 'file-code' };
  return icons[type] || 'file';
}

function formatDate(iso) {
  if (!iso) return '';
  try { return new Date(iso).toLocaleDateString(); } catch { return ''; }
}

async function deleteDocument(docId) {
  if (!confirm('Delete this document from the knowledge base?')) return;
  try {
    await fetch(`/api/knowledge/${docId}`, { method: 'DELETE' });
    showToast('Document deleted', 'success');
    loadKnowledgeBase();
  } catch { showToast('Delete failed', 'error'); }
}

// ── Workflows ────────────────────────────────────────────────────────────────

let currentWorkflowId = null;

async function loadWorkflows() {
  const list = document.getElementById('workflow-list');
  const detail = document.getElementById('workflow-detail');
  if (!list) return;

  // Show list, hide detail
  list.classList.remove('hidden');
  detail.classList.add('hidden');

  try {
    const res = await fetch('/api/workflows');
    const data = await res.json();
    const workflows = data.workflows || [];

    if (workflows.length === 0) {
      list.innerHTML = `
        <div class="empty-state">
          <i data-lucide="workflow" class="empty-icon"></i>
          <p>No workflows configured yet</p>
        </div>`;
    } else {
      list.innerHTML = workflows.map(w => `
        <button class="workflow-card" onclick="openWorkflow(${w.id})" type="button">
          <div class="workflow-card-icon">
            <i data-lucide="${w.is_preset ? 'shield' : 'git-branch'}"></i>
          </div>
          <div class="workflow-card-info">
            <div class="workflow-card-title">
              <strong>${escapeHtml(w.name)}</strong>
              ${w.is_preset ? '<span class="preset-badge">Preset</span>' : ''}
            </div>
            <span class="workflow-card-desc">${escapeHtml(w.description || 'No description')}</span>
            <div class="workflow-card-meta">
              <span>${w.steps?.length || 0} steps</span>
              <span>·</span>
              <span>on_error: ${escapeHtml(w.on_error)}</span>
            </div>
          </div>
          <div class="workflow-card-arrow"><i data-lucide="chevron-right"></i></div>
        </button>
      `).join('');
    }

    if (window.lucide) lucide.createIcons();
  } catch {
    list.innerHTML = '<p style="color:var(--text-3);text-align:center;padding:2rem">Could not load workflows</p>';
  }
}

async function openWorkflow(id) {
  const list = document.getElementById('workflow-list');
  const detail = document.getElementById('workflow-detail');

  try {
    const res = await fetch(`/api/workflows/${id}`);
    const wf = await res.json();
    currentWorkflowId = id;

    // Hide list, show detail
    list.classList.add('hidden');
    detail.classList.remove('hidden');

    // Populate header
    document.getElementById('wf-detail-name').textContent = wf.name;
    document.getElementById('wf-detail-desc').textContent = wf.description || '';
    document.getElementById('wf-detail-badge').textContent = wf.is_preset ? 'Preset' : 'Custom';
    document.getElementById('wf-detail-badge').className = `status-pill ${wf.is_preset ? 'ok' : 'info'}`;

    // Render steps visualization
    const stepsViz = document.getElementById('wf-steps-viz');
    const steps = wf.steps || [];
    stepsViz.innerHTML = steps.map((step, i) => `
      <div class="wf-step-card" id="wf-step-${i}">
        <div class="wf-step-number">${i + 1}</div>
        <div class="wf-step-info">
          <div class="wf-step-id">${escapeHtml(step.step_id)}</div>
          <div class="wf-step-tool"><i data-lucide="wrench"></i> ${escapeHtml(step.tool_name)}</div>
          ${Object.keys(step.input_template || {}).length ? `<div class="wf-step-template"><code>${escapeHtml(JSON.stringify(step.input_template))}</code></div>` : ''}
        </div>
        <div class="wf-step-status" id="wf-step-status-${i}"></div>
      </div>
      ${i < steps.length - 1 ? '<div class="wf-step-connector"><i data-lucide="arrow-down"></i></div>' : ''}
    `).join('');

    // Generate smart default input
    const firstStep = steps[0];
    let defaultInput = {};
    if (firstStep?.input_template) {
      const tmpl = firstStep.input_template;
      for (const [key, val] of Object.entries(tmpl)) {
        if (typeof val === 'string' && val.startsWith('$input')) {
          const field = val.replace('$input.', '').replace('$input', 'text');
          defaultInput[field] = '';
        }
      }
    }
    if (Object.keys(defaultInput).length === 0) defaultInput = { text: '' };
    document.getElementById('wf-run-input').value = JSON.stringify(defaultInput, null, 2);

    // Clear previous results
    document.getElementById('wf-run-result').innerHTML = '';

    if (window.lucide) lucide.createIcons();
  } catch (e) {
    showToast('Failed to load workflow', 'error');
  }
}

function showWorkflowList() {
  document.getElementById('workflow-list').classList.remove('hidden');
  document.getElementById('workflow-detail').classList.add('hidden');
  currentWorkflowId = null;
}

async function runWorkflow() {
  if (!currentWorkflowId) { showToast('Select a workflow first', 'error'); return; }

  const inputEl = document.getElementById('wf-run-input');
  const resultEl = document.getElementById('wf-run-result');
  const btn = document.getElementById('btn-wf-run');

  let input = {};
  try {
    input = JSON.parse(inputEl.value || '{}');
  } catch {
    showToast('Invalid JSON input', 'error');
    return;
  }

  btn.disabled = true;
  resultEl.innerHTML = '<div class="loading-spinner"></div> Running workflow...';

  // Reset step statuses
  document.querySelectorAll('[id^="wf-step-status-"]').forEach(el => {
    el.innerHTML = '';
    el.closest('.wf-step-card').classList.remove('wf-step-done', 'wf-step-error', 'wf-step-running');
  });

  try {
    const res = await fetch(`/api/workflows/${currentWorkflowId}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input }),
    });
    const data = await res.json();
    const result = data.data || data;

    // Update step statuses
    const steps = result.steps || [];
    steps.forEach((step, i) => {
      const statusEl = document.getElementById(`wf-step-status-${i}`);
      const cardEl = document.getElementById(`wf-step-${i}`);
      if (statusEl && cardEl) {
        if (step.status === 'success') {
          statusEl.innerHTML = `<span class="wf-step-ok">✓</span><span class="wf-step-time">${step.duration_ms}ms</span>`;
          cardEl.classList.add('wf-step-done');
        } else {
          statusEl.innerHTML = `<span class="wf-step-err">✗</span>`;
          cardEl.classList.add('wf-step-error');
        }
      }
    });

    // Render full result
    resultEl.innerHTML = renderWorkflowResult(result);

    showToast(result.status === 'completed' ? 'Workflow completed' : 'Workflow finished with errors', result.status === 'completed' ? 'success' : 'error');
    if (window.lucide) lucide.createIcons();
  } catch (e) {
    resultEl.innerHTML = `<div style="color:var(--red)">Error: ${escapeHtml(e.message)}</div>`;
    showToast('Workflow run failed', 'error');
  }

  btn.disabled = false;
}

function renderWorkflowResult(result) {
  const steps = result.steps || [];
  const successCount = steps.filter(s => s.status === 'success').length;

  let html = `
    <div class="scenario-result">
      <div class="result-header">
        <h3>Workflow Result</h3>
        <span class="status-pill ${result.status === 'completed' ? 'ok' : 'warn'}">
          ${escapeHtml(result.status || 'unknown')}
        </span>
      </div>
      <div class="result-grid two-col">
        <div class="result-card">
          <h4>Summary</h4>
          <div class="metric-row"><span>Steps</span><strong>${steps.length}</strong></div>
          <div class="metric-row"><span>Successful</span><strong>${successCount}/${steps.length}</strong></div>
          <div class="metric-row"><span>Total Duration</span><strong>${result.total_duration_ms || 0}ms</strong></div>
        </div>
        <div class="result-card">
          <h4>Final Output</h4>
          <pre style="max-height:200px;overflow:auto;font-size:0.78rem">${escapeHtml(JSON.stringify(result.final_output || {}, null, 2))}</pre>
        </div>
      </div>`;

  // Step-by-step details
  steps.forEach((step, i) => {
    const isSuccess = step.status === 'success';
    html += `
      <div class="result-card">
        <h4>
          <span class="wf-step-indicator ${isSuccess ? 'ok' : 'err'}">${isSuccess ? '✓' : '✗'}</span>
          Step ${i + 1}: ${escapeHtml(step.step_id)} → ${escapeHtml(step.tool_name)}
          <span class="wf-step-duration">${step.duration_ms}ms</span>
        </h4>
        <pre style="max-height:150px;overflow:auto;font-size:0.75rem">${escapeHtml(JSON.stringify(step.output || step.error || {}, null, 2))}</pre>
      </div>`;
  });

  html += '</div>';
  return html;
}

// ── Tool Functions (Process, Analyze, Extract, Summarize, Pipeline) ─────────

async function runProcess() {
  const text = document.getElementById('process-text').value.trim();
  if (!text) { showToast('Paste a document to process', 'error'); return; }

  const docType = document.getElementById('process-type').value;
  const steps = document.getElementById('process-steps');
  const result = document.getElementById('process-result');
  steps.classList.remove('hidden');
  result.innerHTML = '';

  const stepEls = steps.querySelectorAll('.process-step');
  stepEls.forEach(s => { s.classList.remove('active', 'done'); s.querySelector('.step-icon').className = 'step-icon pending'; s.querySelector('.step-icon').textContent = '○'; s.querySelector('.step-time').textContent = ''; });

  const btn = document.getElementById('btn-process');
  btn.disabled = true;

  try {
    const startTime = Date.now();
    const stepNames = ['analyze', 'extract', 'summarize', 'validate'];
    stepNames.forEach((name, i) => {
      setTimeout(() => {
        stepEls[i].classList.add('active');
        stepEls[i].querySelector('.step-icon').className = 'step-icon running';
        stepEls[i].querySelector('.step-icon').textContent = '◉';
      }, i * 200);
    });

    const res = await fetch('/api/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, document_type: docType }),
    });
    const data = await res.json();
    const elapsed = Date.now() - startTime;

    stepEls.forEach((s, i) => {
      s.classList.remove('active');
      s.classList.add('done');
      s.querySelector('.step-icon').className = 'step-icon done';
      s.querySelector('.step-icon').textContent = '✓';
      s.querySelector('.step-time').textContent = `${Math.round(elapsed / 4 * (i + 1))}ms`;
    });

    result.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    showToast('Document processed successfully', 'success');
  } catch (e) {
    result.innerHTML = `<div style="color:var(--red)">Error: ${e.message}</div>`;
    showToast('Processing failed', 'error');
  }
  btn.disabled = false;
}

async function runAnalyze() {
  const text = document.getElementById('analyze-text').value.trim();
  if (!text) { showToast('Paste text to analyze', 'error'); return; }

  const focus = document.getElementById('analyze-focus').value;
  const result = document.getElementById('analyze-result');
  const btn = document.getElementById('btn-analyze');
  btn.disabled = true;
  result.innerHTML = '<div class="loading-spinner"></div>';

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, focus }),
    });
    const data = await res.json();
    result.innerHTML = renderAnalyzeResult(data);
    showToast('Analysis complete', 'success');
    if (window.lucide) lucide.createIcons();
  } catch (e) {
    result.innerHTML = `<div style="color:var(--red)">Error: ${e.message}</div>`;
  }
  btn.disabled = false;
}

async function runExtract() {
  const text = document.getElementById('extract-text').value.trim();
  if (!text) { showToast('Paste text to extract from', 'error'); return; }

  const fieldsRaw = document.getElementById('extract-fields').value;
  const strategy = document.getElementById('extract-strategy').value;
  const fields = fieldsRaw ? fieldsRaw.split(',').map(f => f.trim()).filter(Boolean) : [];
  const result = document.getElementById('extract-result');
  const btn = document.getElementById('btn-extract');
  btn.disabled = true;
  result.innerHTML = '<div class="loading-spinner"></div>';

  try {
    const res = await fetch('/api/extract', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, fields, strategy }),
    });
    const data = await res.json();
    result.innerHTML = renderExtractResult(data);
    showToast('Extraction complete', 'success');
    if (window.lucide) lucide.createIcons();
  } catch (e) {
    result.innerHTML = `<div style="color:var(--red)">Error: ${e.message}</div>`;
  }
  btn.disabled = false;
}

async function runSummarize() {
  const text = document.getElementById('summarize-text').value.trim();
  if (!text) { showToast('Paste text to summarize', 'error'); return; }

  const format = document.getElementById('summarize-format').value;
  const maxPoints = parseInt(document.getElementById('summarize-points').value) || 5;
  const result = document.getElementById('summarize-result');
  const btn = document.getElementById('btn-summarize');
  btn.disabled = true;
  result.innerHTML = '<div class="loading-spinner"></div>';

  try {
    const res = await fetch('/api/summarize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, format, max_points: maxPoints }),
    });
    const data = await res.json();
    result.innerHTML = renderSummarizeResult(data);
    showToast('Summary complete', 'success');
  } catch (e) {
    result.innerHTML = `<div style="color:var(--red)">Error: ${e.message}</div>`;
  }
  btn.disabled = false;
}

let selectedPipeline = 'github';
function selectPipeline(name) {
  selectedPipeline = name;
  document.querySelectorAll('.pipeline-card').forEach(c => c.classList.remove('selected'));
  document.getElementById(`pipe-${name}`)?.classList.add('selected');
}

async function runPipeline() {
  const result = document.getElementById('pipeline-result');
  const btn = document.getElementById('btn-pipeline');
  btn.disabled = true;
  result.innerHTML = '<div class="loading-spinner"></div>';

  try {
    const res = await fetch('/api/pipeline', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pipeline: selectedPipeline }),
    });
    const data = await res.json();
    result.innerHTML = renderMarkdown(data.result || JSON.stringify(data, null, 2));
    showToast('Pipeline complete', 'success');
  } catch (e) {
    result.innerHTML = `<div style="color:var(--red)">Error: ${e.message}</div>`;
  }
  btn.disabled = false;
}

// ── Structured Tool Result Renderers ─────────────────────────────────────────

function renderAnalyzeResult(data) {
  const d = data.data || data;
  const method = d.method || 'rule_based';
  const stats = d.statistics || {};
  const entities = d.entities || {};
  const keyPoints = d.key_points || [];
  const sections = d.sections || [];

  return `
    <div class="scenario-result">
      <div class="result-header">
        <h3>Document Analysis</h3>
        <div style="display:flex;gap:0.4rem">
          <span class="status-pill ok">${escapeHtml(d.document_type || 'unknown')}</span>
          <span class="status-pill ${method === 'ai' ? 'info' : 'ok'}">${method === 'ai' ? '🤖 AI' : '📏 Rule-based'}</span>
        </div>
      </div>

      <div class="result-grid two-col">
        <div class="result-card">
          <h4>Statistics</h4>
          <div class="metric-row"><span>Words</span><strong>${stats.word_count || 0}</strong></div>
          <div class="metric-row"><span>Sentences</span><strong>${stats.sentence_count || 0}</strong></div>
          <div class="metric-row"><span>Paragraphs</span><strong>${stats.paragraph_count || 0}</strong></div>
          <div class="metric-row"><span>Lines</span><strong>${stats.line_count || 0}</strong></div>
          <div class="metric-row"><span>Focus</span><strong>${escapeHtml(d.focus || 'general')}</strong></div>
        </div>
        <div class="result-card">
          <h4>Key Points</h4>
          ${keyPoints.length ? `<ul class="key-points-list">${keyPoints.map(p => `<li>${escapeHtml(p)}</li>`).join('')}</ul>` : '<p class="muted">No key points extracted.</p>'}
        </div>
      </div>

      ${sections.length ? `
      <div class="result-card">
        <h4>Document Structure</h4>
        <div class="section-tree">${sections.map(s => `<div class="section-item" style="padding-left:${(s.level - 1) * 1.2}rem"><span class="section-level">H${s.level}</span> ${escapeHtml(s.title)}</div>`).join('')}</div>
      </div>` : ''}

      ${Object.values(entities).some(v => v.length > 0) ? `
      <div class="result-card">
        <h4>Entities</h4>
        ${renderEntityBadges(entities)}
      </div>` : ''}

      ${d.summary ? `
      <div class="result-card">
        <h4>AI Summary</h4>
        <p style="font-size:0.85rem;line-height:1.5">${escapeHtml(d.summary)}</p>
      </div>` : ''}
    </div>
  `;
}

function renderExtractResult(data) {
  const d = data.data || data;
  const method = d.method || 'rule_based';
  const extracted = d.extracted || {};
  const entries = Object.entries(extracted);

  return `
    <div class="scenario-result">
      <div class="result-header">
        <h3>Data Extraction</h3>
        <div style="display:flex;gap:0.4rem">
          <span class="status-pill ${d.fields_missing === 0 ? 'ok' : 'warn'}">${d.fields_found || 0}/${entries.length} found</span>
          <span class="status-pill ${method === 'ai' ? 'info' : 'ok'}">${method === 'ai' ? '🤖 AI-assisted' : '📏 Rule-based'}</span>
        </div>
      </div>

      <div class="result-card">
        <h4>Extracted Fields</h4>
        <div class="extract-table">
          ${entries.map(([key, val]) => `
            <div class="extract-row">
              <span class="extract-field">${escapeHtml(key)}</span>
              <span class="extract-value ${val === null ? 'missing' : 'found'}">
                ${val !== null ? escapeHtml(String(val)) : 'Not found'}
              </span>
              ${d.ai_assisted_fields?.includes(key) ? '<span class="extract-ai-badge">AI</span>' : ''}
            </div>
          `).join('')}
        </div>
      </div>

      <div class="result-card">
        <h4>Strategy</h4>
        <div class="metric-row"><span>Strategy</span><strong>${escapeHtml(d.strategy || 'auto')}</strong></div>
        ${d.strategies_used ? `<div class="metric-row"><span>Strategies used</span><strong>${d.strategies_used.join(', ')}</strong></div>` : ''}
        <div class="metric-row"><span>Fields found</span><strong>${d.fields_found || 0}</strong></div>
        <div class="metric-row"><span>Fields missing</span><strong>${d.fields_missing || 0}</strong></div>
      </div>
    </div>
  `;
}

function renderSummarizeResult(data) {
  const d = data.data || data;
  const method = d.method || 'extractive';
  const format = d.format || 'bullets';
  const wordCount = d.original_word_count || 0;
  const sentenceCount = d.sentence_count || 0;
  const summary = d.summary || '';

  // Estimate summary word count for compression ratio
  const summaryWordCount = summary.split(/\s+/).filter(Boolean).length;
  const compression = wordCount > 0 ? Math.round((1 - summaryWordCount / wordCount) * 100) : 0;

  // Render summary content based on format
  let summaryHtml;
  if (format === 'bullets' && summary.includes('- ')) {
    const points = summary.split('\n').filter(l => l.trim().startsWith('- '));
    summaryHtml = `<ul class="summary-points">${points.map(p => `<li>${escapeHtml(p.replace(/^-\s*/, ''))}</li>`).join('')}</ul>`;
  } else {
    summaryHtml = `<p class="summary-paragraph">${escapeHtml(summary)}</p>`;
  }

  return `
    <div class="scenario-result">
      <div class="result-header">
        <h3>Summarization</h3>
        <div style="display:flex;gap:0.4rem">
          <span class="status-pill ${method === 'ai' ? 'info' : 'ok'}">${method === 'ai' ? '🤖 AI' : '📏 Extractive'}</span>
          <span class="status-pill ok">${format === 'bullets' ? '• Bullets' : '¶ Paragraph'}</span>
        </div>
      </div>

      <div class="result-grid two-col">
        <div class="result-card">
          <h4>Document Stats</h4>
          <div class="metric-row"><span>Original words</span><strong>${wordCount.toLocaleString()}</strong></div>
          <div class="metric-row"><span>Sentences analyzed</span><strong>${sentenceCount}</strong></div>
          <div class="metric-row"><span>Summary words</span><strong>${summaryWordCount}</strong></div>
          <div class="metric-row"><span>Compression</span><strong>${compression}% reduced</strong></div>
        </div>
        <div class="result-card">
          <h4>Summary</h4>
          ${summaryHtml}
        </div>
      </div>
    </div>
  `;
}

// ── Chat ─────────────────────────────────────────────────────────────────────

function sendSuggestion(btn) {
  document.getElementById('chat-input').value = btn.textContent;
  sendChat();
}

async function sendChat() {
  const input = document.getElementById('chat-input');
  const message = input.value.trim();
  if (!message) return;

  const messages = document.getElementById('chat-messages');

  // Clear welcome
  const welcome = messages.querySelector('.chat-welcome');
  if (welcome) welcome.remove();

  // Add user message
  messages.innerHTML += `<div class="chat-msg user">${escapeHtml(message)}</div>`;
  input.value = '';
  messages.scrollTop = messages.scrollHeight;

  // Typing indicator
  messages.innerHTML += '<div class="typing-indicator" id="typing"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>';
  messages.scrollTop = messages.scrollHeight;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    document.getElementById('typing')?.remove();

    if (res.headers.get('content-type')?.includes('text/event-stream')) {
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let fullText = '';
      const msgDiv = document.createElement('div');
      msgDiv.className = 'chat-msg assistant';
      messages.appendChild(msgDiv);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        for (const line of chunk.split('\n')) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'text') {
                fullText += data.content;
                msgDiv.innerHTML = renderMarkdown(fullText);
              } else if (data.type === 'tool_call') {
                msgDiv.innerHTML += `<div class="tool-call-card"><i data-lucide="wrench"></i> Using: ${data.tool_name}</div>`;
              }
            } catch { /* skip */ }
          }
        }
        messages.scrollTop = messages.scrollHeight;
      }
      if (window.lucide) lucide.createIcons();
    } else {
      const data = await res.json();
      messages.innerHTML += `<div class="chat-msg assistant">${renderMarkdown(data.response || JSON.stringify(data))}</div>`;
    }
    messages.scrollTop = messages.scrollHeight;
  } catch (e) {
    document.getElementById('typing')?.remove();
    messages.innerHTML += `<div class="chat-msg assistant" style="border-left:3px solid var(--red)">Error: ${e.message}</div>`;
  }
}

// Chat input: Enter sends, Shift+Enter newline
document.getElementById('chat-input')?.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
});

// ── Utilities ────────────────────────────────────────────────────────────────

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function renderMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/\n/g, '<br>');
}

// ── Keyboard shortcuts ───────────────────────────────────────────────────────

document.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
    e.preventDefault();
    if (currentView === 'process') runProcess();
    else if (currentView === 'analyze') runAnalyze();
    else if (currentView === 'extract') runExtract();
    else if (currentView === 'summarize') runSummarize();
    else if (currentView === 'pipeline') runPipeline();
    else if (currentView === 'chat') sendChat();
    else if (currentView === 'scenario') runScenario();
    else if (currentView === 'workflows') runWorkflow();
  }
});

// ── Load examples ────────────────────────────────────────────────────────────

function loadExample(tool, key) {
  if (!key || !window.EXAMPLES?.[tool]?.[key]) return;
  const data = window.EXAMPLES[tool][key];
  const textarea = document.getElementById(`${tool}-text`);
  if (textarea) textarea.value = data.text || '';

  // Populate tool-specific fields
  const fieldsEl = document.getElementById(`${tool}-fields`);
  if (fieldsEl && data.fields) {
    fieldsEl.value = Array.isArray(data.fields) ? data.fields.join(', ') : data.fields;
  }
  const strategyEl = document.getElementById(`${tool}-strategy`);
  if (strategyEl && data.strategy) strategyEl.value = data.strategy;
  const focusEl = document.getElementById(`${tool}-focus`);
  if (focusEl && data.focus) focusEl.value = data.focus;
  const formatEl = document.getElementById(`${tool}-format`);
  if (formatEl && data.format) formatEl.value = data.format;
  const pointsEl = document.getElementById(`${tool}-points`);
  if (pointsEl && data.max_points) pointsEl.value = data.max_points;
  const typeEl = document.getElementById(`${tool}-type`);
  if (typeEl && data.document_type) typeEl.value = data.document_type;
}

// ── Init ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) lucide.createIcons();
  checkHealth();
  loadDashboard();
});
