// ── Typing hero effect ──────────────────────────────────────────────────────

const HERO_PHRASES = [
  'Process invoices and extract structured data',
  'Analyze documents and detect key entities',
  'Summarize reports into actionable insights',
  'Run automated data pipelines on live APIs',
  'Validate business documents for ERP import',
];

(function initTypingHero() {
  const el = document.getElementById('hero-typed');
  if (!el) return;
  let phraseIndex = 0;
  let charIndex = 0;
  let deleting = false;
  let pauseCounter = 0;

  function tick() {
    const phrase = HERO_PHRASES[phraseIndex];

    if (!deleting) {
      el.textContent = phrase.slice(0, charIndex + 1);
      charIndex++;
      if (charIndex === phrase.length) {
        pauseCounter = 0;
        deleting = true;
        setTimeout(tick, 2000);
        return;
      }
      setTimeout(tick, 45);
    } else {
      el.textContent = phrase.slice(0, charIndex);
      charIndex--;
      if (charIndex === 0) {
        deleting = false;
        phraseIndex = (phraseIndex + 1) % HERO_PHRASES.length;
        setTimeout(tick, 300);
        return;
      }
      setTimeout(tick, 25);
    }
  }

  tick();
})();

// ── Toast notifications ─────────────────────────────────────────────────────

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const icons = { success: '✓', error: '✗', info: 'ℹ' };
  toast.innerHTML = `<span class="toast-icon" aria-hidden="true">${icons[type] || icons.info}</span><span class="toast-text">${message}</span>`;

  container.appendChild(toast);

  // Trigger animation
  requestAnimationFrame(() => toast.classList.add('visible'));

  setTimeout(() => {
    toast.classList.remove('visible');
    toast.addEventListener('transitionend', () => toast.remove());
  }, 3000);
}

// ── Keyboard shortcuts ──────────────────────────────────────────────────────

document.addEventListener('keydown', (e) => {
  // Cmd/Ctrl + Enter → run active tool
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
    e.preventDefault();
    const activePanel = document.querySelector('.tool-panel.active');
    if (!activePanel) return;

    const toolId = activePanel.id.replace('panel-', '');
    const runners = {
      process: runProcess,
      analyze: runAnalyze,
      extract: runExtract,
      summarize: runSummarize,
      pipeline: runPipeline,
    };

    if (runners[toolId]) runners[toolId]();
  }

  // Number keys 1-5 to switch tabs (when not in a text input)
  if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;
  const tabKeys = { '1': 'process', '2': 'analyze', '3': 'extract', '4': 'summarize', '5': 'pipeline', '6': 'chat' };
  if (tabKeys[e.key]) {
    e.preventDefault();
    switchToTool(tabKeys[e.key]);
  }
});

// ── Tab navigation ──────────────────────────────────────────────────────────

document.querySelectorAll('.tool-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    switchToTool(tab.dataset.tool);
  });
});

// ── Pipeline selection ──────────────────────────────────────────────────────

let selectedPipeline = 'github';

function selectPipeline(name) {
  selectedPipeline = name;
  document.querySelectorAll('.pipeline-card').forEach(c => c.classList.remove('selected'));
  document.getElementById(`pipe-${name}`).classList.add('selected');
}

// ── Health check ────────────────────────────────────────────────────────────

async function checkHealth() {
  const bar = document.getElementById('status-bar');
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    if (data.api_key_configured) {
      bar.innerHTML = '<span class="status-dot ok"></span> Connected — AI summarization enabled';
    } else {
      bar.innerHTML = '<span class="status-dot warn"></span> Running in demo mode — extractive summarization';
    }
    updateChatBadge(data.api_key_configured);
  } catch {
    bar.innerHTML = '<span class="status-dot err"></span> Server not reachable';
  }
}

checkHealth();

// Update keyboard hints for non-Mac
if (!navigator.platform.includes('Mac')) {
  document.querySelectorAll('.kbd-hint').forEach(el => {
    el.textContent = 'Ctrl↵';
  });
}

// ── Loading states ──────────────────────────────────────────────────────────

const LOADING_MESSAGES = {
  analyze: [
    'Detecting document type...',
    'Extracting entities...',
    'Identifying key points...',
    'Computing statistics...',
  ],
  extract: [
    'Scanning for fields...',
    'Applying extraction strategy...',
    'Matching field values...',
  ],
  summarize: [
    'Analyzing text structure...',
    'Identifying key sentences...',
    'Generating summary...',
  ],
  pipeline: [
    'Starting TypeScript pipeline...',
    'Fetching data from API...',
    'Cleaning and filtering records...',
    'Aggregating results...',
    'Formatting output...',
  ],
};

function showLoading(tool) {
  const overlay = document.getElementById('loading-overlay');
  const message = document.getElementById('loading-message');
  overlay.classList.remove('hidden');

  const messages = LOADING_MESSAGES[tool] || ['Processing...'];
  let i = 0;
  message.textContent = messages[0];

  const interval = setInterval(() => {
    i++;
    if (i < messages.length) {
      message.textContent = messages[i];
    }
  }, 600);

  overlay.dataset.interval = interval;
}

function hideLoading() {
  const overlay = document.getElementById('loading-overlay');
  overlay.classList.add('hidden');
  clearInterval(overlay.dataset.interval);
}

// ── Button loading states ────────────────────────────────────────────────────

function setButtonLoading(tool, loading) {
  const btnMap = {
    analyze: 'btn-analyze',
    extract: 'btn-extract',
    summarize: 'btn-summarize',
    pipeline: 'btn-pipeline',
    process: 'btn-process',
  };
  const btn = document.getElementById(btnMap[tool]);
  if (!btn) return;

  if (loading) {
    btn.disabled = true;
    btn.classList.add('loading');
    btn.querySelector('.btn-label').dataset.original = btn.querySelector('.btn-label').textContent;
    btn.querySelector('.btn-label').textContent = 'Running...';
  } else {
    btn.disabled = false;
    btn.classList.remove('loading');
    const label = btn.querySelector('.btn-label');
    if (label.dataset.original) {
      label.textContent = label.dataset.original;
    }
  }
}

// ── API call ────────────────────────────────────────────────────────────────

async function callAPI(endpoint, body, tool) {
  showLoading(tool);
  setButtonLoading(tool, true);
  hideResult();

  const start = performance.now();

  try {
    const res = await fetch(`/api/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const elapsed = Math.round(performance.now() - start);

    if (!res.ok) {
      const err = await res.json();
      hideLoading();
      setButtonLoading(tool, false);
      showError(err.detail || `Request failed (${res.status})`);
      showToast(err.detail || `Request failed (${res.status})`, 'error');
      return null;
    }

    const data = await res.json();
    hideLoading();
    setButtonLoading(tool, false);
    document.getElementById('result-time').textContent = `${elapsed}ms`;
    showToast(`${tool.charAt(0).toUpperCase() + tool.slice(1)} completed in ${elapsed}ms`, 'success');
    return data;
  } catch (err) {
    hideLoading();
    setButtonLoading(tool, false);
    showError(`Network error: ${err.message}`);
    showToast('Network error — is the server running?', 'error');
    return null;
  }
}

// ── Document processing ─────────────────────────────────────────────────────

async function runProcess() {
  const text = document.getElementById('process-text').value.trim();
  if (!text) { flash('process-text'); return; }

  const docType = document.getElementById('process-type').value;
  const stepsEl = document.getElementById('process-steps');
  const stepNodes = stepsEl.querySelectorAll('.process-step');

  // Reset and show step tracker
  stepNodes.forEach(node => {
    node.querySelector('.step-icon').className = 'step-icon pending';
    node.querySelector('.step-icon').textContent = '○';
    node.querySelector('.step-time').textContent = '';
    node.classList.remove('done', 'active');
  });
  stepsEl.classList.remove('hidden');
  setButtonLoading('process', true);
  hideResult();

  // Animate steps sequentially while waiting for API
  const stepNames = ['analyze', 'extract', 'summarize', 'validate'];
  let currentStep = 0;

  function activateStep(index) {
    if (index >= stepNames.length) return;
    const node = stepNodes[index];
    node.classList.add('active');
    node.querySelector('.step-icon').className = 'step-icon running';
    node.querySelector('.step-icon').textContent = '◌';
  }

  activateStep(0);
  const stepInterval = setInterval(() => {
    if (currentStep < stepNames.length) {
      const node = stepNodes[currentStep];
      node.classList.remove('active');
      node.classList.add('done');
      node.querySelector('.step-icon').className = 'step-icon done';
      node.querySelector('.step-icon').textContent = '✓';
      currentStep++;
      activateStep(currentStep);
    }
  }, 400);

  const start = performance.now();

  try {
    const res = await fetch('/api/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, document_type: docType }),
    });

    clearInterval(stepInterval);
    const elapsed = Math.round(performance.now() - start);

    if (!res.ok) {
      const err = await res.json();
      resetProcessSteps();
      setButtonLoading('process', false);
      showError(err.detail || `Request failed (${res.status})`);
      showToast(err.detail || 'Processing failed', 'error');
      return;
    }

    const data = await res.json();

    // Update steps with actual results
    data.data.steps.forEach((step, i) => {
      const node = stepNodes[i];
      node.classList.remove('active');
      node.classList.add('done');
      node.querySelector('.step-icon').className = 'step-icon done';
      node.querySelector('.step-icon').textContent = '✓';
      node.querySelector('.step-time').textContent = `${step.duration_ms}ms`;
    });

    document.getElementById('result-time').textContent = `${elapsed}ms`;
    setButtonLoading('process', false);
    showToast(`Document processed in ${elapsed}ms`, 'success');
    renderProcess(data.data);
  } catch (err) {
    clearInterval(stepInterval);
    resetProcessSteps();
    setButtonLoading('process', false);
    showError(`Network error: ${err.message}`);
    showToast('Network error — is the server running?', 'error');
  }
}

function resetProcessSteps() {
  const stepsEl = document.getElementById('process-steps');
  stepsEl.classList.add('hidden');
}

function renderProcess(d) {
  const analysis = d.steps[0].data;
  const extraction = d.steps[1].data;
  const summary = d.steps[2].data;
  const validation = d.steps[3].data;

  const allEntities = [
    ...analysis.entities.emails.map(e => ({ icon: '📧', label: 'Email', value: e })),
    ...analysis.entities.dates.map(e => ({ icon: '📅', label: 'Date', value: e })),
    ...analysis.entities.urls.map(e => ({ icon: '🔗', label: 'URL', value: e })),
    ...analysis.entities.organizations.map(e => ({ icon: '🏢', label: 'Org', value: e })),
  ];

  const found = Object.entries(extraction.extracted).filter(([, v]) => v !== null);
  const missing = Object.entries(extraction.extracted).filter(([, v]) => v === null);

  const confidencePct = Math.round(d.confidence * 100);
  const confidenceColor = confidencePct >= 80 ? 'high' : confidencePct >= 50 ? 'mid' : 'low';

  const severityIcon = { error: '❌', warning: '⚠️', info: 'ℹ️', pass: '✅' };

  setResultHeader('Document Processing Report',
    `${d.steps.length} processing steps completed in ${d.total_duration_ms}ms`);

  const html = `
    <div class="process-report">

      <!-- Smart summary (if available) -->
      ${summary.smart_summary ? `
        <div class="smart-summary">
          <span class="smart-summary-icon">📄</span>
          <p>${esc(summary.smart_summary)}</p>
        </div>
      ` : ''}

      <!-- Overview card -->
      <div class="process-overview">
        <div class="overview-stat">
          <span class="overview-label">Document Type</span>
          <span class="tag type-tag">${d.document_type.replace(/_/g, ' ')}</span>
        </div>
        <div class="overview-stat">
          <span class="overview-label">Fields Extracted</span>
          <span class="overview-value">${d.fields_extracted}</span>
        </div>
        <div class="overview-stat">
          <span class="overview-label">Entities Found</span>
          <span class="overview-value">${d.entities_found}</span>
        </div>
        <div class="overview-stat">
          <span class="overview-label">Confidence</span>
          <div class="confidence-bar">
            <div class="confidence-fill ${confidenceColor}" style="width: ${confidencePct}%"></div>
          </div>
          <span class="confidence-label">${confidencePct}%</span>
        </div>
      </div>

      <!-- Step 1: Analysis -->
      <div class="process-section">
        <div class="process-section-header">
          <span class="process-section-icon">🔍</span>
          <h4>Analysis</h4>
          <span class="step-badge">${d.steps[0].duration_ms}ms</span>
        </div>
        <div class="process-section-body">
          <div class="result-grid">
            <div class="result-card">
              <h4>Statistics</h4>
              ${statRow('Words', analysis.statistics.word_count)}
              ${statRow('Sentences', analysis.statistics.sentence_count)}
              ${statRow('Paragraphs', analysis.statistics.paragraph_count)}
              ${statRow('Lines', analysis.statistics.line_count)}
            </div>
            <div class="result-card">
              <h4>Structure</h4>
              ${analysis.sections.length > 0
                ? `<div class="section-tree">${analysis.sections.map(s =>
                    `<div class="section-item level-${s.level}"><span class="section-marker">H${s.level}</span>${esc(s.title)}</div>`
                  ).join('')}</div>`
                : `<p class="empty-state">No heading structure detected</p>`}
            </div>
            ${allEntities.length > 0 ? `
              <div class="result-card full-width">
                <h4>Entities <span class="count-badge">${allEntities.length}</span></h4>
                <div class="entity-grid">${allEntities.map(e =>
                  `<div class="entity-item"><span class="entity-icon">${e.icon}</span><div><span class="entity-label">${e.label}</span><span class="entity-value">${esc(e.value)}</span></div></div>`
                ).join('')}</div>
              </div>
            ` : ''}
          </div>
        </div>
      </div>

      <!-- Step 2: Extraction -->
      <div class="process-section">
        <div class="process-section-header">
          <span class="process-section-icon">📋</span>
          <h4>Extraction</h4>
          <span class="step-badge">${d.steps[1].duration_ms}ms</span>
        </div>
        <div class="process-section-body">
          <table class="data-table">
            <thead><tr><th>Field</th><th>Value</th><th>Status</th></tr></thead>
            <tbody>
              ${found.map(([k, v]) => `
                <tr>
                  <td class="field-name">${esc(k)}</td>
                  <td class="field-value">${esc(String(v))}</td>
                  <td><span class="status-pill ok">found</span></td>
                </tr>
              `).join('')}
              ${missing.map(([k]) => `
                <tr class="missing-row">
                  <td class="field-name">${esc(k)}</td>
                  <td class="field-value empty">—</td>
                  <td><span class="status-pill miss">missing</span></td>
                </tr>
              `).join('')}
            </tbody>
          </table>
          <div class="extraction-summary">
            <span class="tag">${extraction.strategy} strategy</span>
            ${(extraction.strategies_used || []).map(s => `<span class="tag">${s}</span>`).join('')}
          </div>
        </div>
      </div>

      <!-- Step 3: Summary -->
      <div class="process-section">
        <div class="process-section-header">
          <span class="process-section-icon">✏️</span>
          <h4>Summary</h4>
          <span class="step-badge">${d.steps[2].duration_ms}ms</span>
        </div>
        <div class="process-section-body">
          <div class="summary-text">${formatSummary(summary.summary)}</div>
          <div class="summary-meta">
            <span class="tag">${summary.method === 'ai' ? '🤖 AI-powered' : '📝 Extractive'}</span>
            <span class="tag">${summary.format}</span>
            <span class="tag">${summary.original_word_count} words → ${summary.summary.split(/\s+/).length} words</span>
          </div>
        </div>
      </div>

      <!-- Step 4: Validation -->
      <div class="process-section">
        <div class="process-section-header">
          <span class="process-section-icon">${d.validation_errors > 0 ? '⚠️' : '✅'}</span>
          <h4>Validation</h4>
          <span class="step-badge">${d.steps[3].duration_ms}ms</span>
        </div>
        <div class="process-section-body">
          ${validation.issues.length > 0 ? `
            <div class="validation-list">
              ${validation.issues.map(issue => `
                <div class="validation-item ${issue.severity}">
                  <span class="validation-icon">${severityIcon[issue.severity] || 'ℹ️'}</span>
                  <div class="validation-content">
                    <span class="validation-field">${esc(issue.field)}</span>
                    <span class="validation-message">${esc(issue.message)}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          ` : '<p class="empty-state">No validation issues found</p>'}
        </div>
      </div>

      <!-- ERP Output -->
      <div class="process-section">
        <div class="process-section-header">
          <span class="process-section-icon">🔗</span>
          <h4>ERP-Ready Output</h4>
          <div class="erp-actions">
            <button class="btn-small" onclick="copyErpOutput('json', this)">Copy JSON</button>
            <button class="btn-small" onclick="copyErpOutput('csv', this)">Copy CSV</button>
          </div>
        </div>
        <div class="process-section-body">
          <p class="erp-description">Structured payload ready for import into ERP systems (Infor M3, Business Central, SAP) or downstream processing via API.</p>
          <pre class="erp-json" id="erp-json-output">${esc(JSON.stringify(d.erp_output, null, 2))}</pre>
        </div>
      </div>

    </div>
  `;
  showResult(html);
}

function copyErpOutput(format, btn) {
  const data = JSON.parse(document.getElementById('erp-json-output').textContent);
  let text;

  if (format === 'csv') {
    const fields = data.extracted_fields;
    const headers = Object.keys(fields).join(',');
    const values = Object.values(fields).map(v => `"${v}"`).join(',');
    text = `${headers}\n${values}`;
  } else {
    text = JSON.stringify(data, null, 2);
  }

  navigator.clipboard.writeText(text).then(() => {
    const original = btn.textContent;
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = original;
      btn.classList.remove('copied');
    }, 1500);
  });
}

// ── Tool runners ────────────────────────────────────────────────────────────

async function runAnalyze() {
  const text = document.getElementById('analyze-text').value.trim();
  if (!text) { flash('analyze-text'); return; }

  const data = await callAPI('analyze', {
    text,
    focus: document.getElementById('analyze-focus').value,
  }, 'analyze');

  if (data) renderAnalyze(data.data);
}

async function runExtract() {
  const text = document.getElementById('extract-text').value.trim();
  const fieldsStr = document.getElementById('extract-fields').value.trim();
  if (!text) { flash('extract-text'); return; }
  if (!fieldsStr) { flash('extract-fields'); return; }

  const fields = fieldsStr.split(',').map(f => f.trim()).filter(Boolean);
  const data = await callAPI('extract', {
    text,
    fields,
    strategy: document.getElementById('extract-strategy').value,
  }, 'extract');

  if (data) renderExtract(data.data);
}

async function runSummarize() {
  const text = document.getElementById('summarize-text').value.trim();
  if (!text) { flash('summarize-text'); return; }

  const data = await callAPI('summarize', {
    text,
    format: document.getElementById('summarize-format').value,
    max_points: parseInt(document.getElementById('summarize-points').value),
  }, 'summarize');

  if (data) renderSummarize(data.data);
}

async function runPipeline() {
  const data = await callAPI('pipeline', {
    task: `Run ${selectedPipeline} analysis pipeline`,
    pipeline: selectedPipeline,
  }, 'pipeline');

  if (data) renderPipeline(data.data);
}

// ── Renderers ───────────────────────────────────────────────────────────────

function renderAnalyze(d) {
  const entities = d.entities;
  const allEntities = [
    ...entities.emails.map(e => ({ icon: '📧', label: 'Email', value: e })),
    ...entities.dates.map(e => ({ icon: '📅', label: 'Date', value: e })),
    ...entities.urls.map(e => ({ icon: '🔗', label: 'URL', value: e })),
    ...entities.organizations.map(e => ({ icon: '🏢', label: 'Org', value: e })),
  ];

  setResultHeader('Document Analysis',
    `Detected as "${d.document_type.replace(/_/g, ' ')}" with focus on ${d.focus}`);

  const html = `
    <div class="result-grid">
      <div class="result-card">
        <h4>Document Type</h4>
        <span class="tag type-tag">${d.document_type.replace(/_/g, ' ')}</span>
      </div>
      <div class="result-card">
        <h4>Statistics</h4>
        ${statRow('Words', d.statistics.word_count)}
        ${statRow('Sentences', d.statistics.sentence_count)}
        ${statRow('Paragraphs', d.statistics.paragraph_count)}
        ${statRow('Lines', d.statistics.line_count)}
      </div>
      <div class="result-card${allEntities.length > 4 ? ' full-width' : ''}">
        <h4>Entities Found <span class="count-badge">${allEntities.length}</span></h4>
        ${allEntities.length > 0
          ? `<div class="entity-grid">${allEntities.map(e =>
              `<div class="entity-item"><span class="entity-icon">${e.icon}</span><div><span class="entity-label">${e.label}</span><span class="entity-value">${esc(e.value)}</span></div></div>`
            ).join('')}</div>`
          : '<p class="empty-state">No entities detected in this text</p>'}
      </div>
      ${d.sections.length > 0 ? `
        <div class="result-card">
          <h4>Document Structure</h4>
          <div class="section-tree">${d.sections.map(s =>
            `<div class="section-item level-${s.level}"><span class="section-marker">H${s.level}</span>${esc(s.title)}</div>`
          ).join('')}</div>
        </div>
      ` : ''}
      ${d.key_points.length > 0 ? `
        <div class="result-card full-width">
          <h4>Key Points</h4>
          <div class="key-points-list">${d.key_points.map(p =>
            `<div class="key-point"><span class="kp-marker">▸</span><span>${esc(p)}</span></div>`
          ).join('')}</div>
        </div>
      ` : ''}
    </div>
  `;
  showResult(html);
}

function renderExtract(d) {
  const found = Object.entries(d.extracted).filter(([, v]) => v !== null);
  const missing = Object.entries(d.extracted).filter(([, v]) => v === null);

  setResultHeader('Extracted Data',
    `Found ${d.fields_found} of ${d.fields_found + d.fields_missing} fields using ${d.strategy} strategy`);

  const html = `
    <div class="result-grid">
      <div class="result-card full-width">
        <h4>Extracted Fields</h4>
        <table class="data-table">
          <thead><tr><th>Field</th><th>Value</th><th>Status</th></tr></thead>
          <tbody>
            ${found.map(([k, v]) => `
              <tr>
                <td class="field-name">${esc(k)}</td>
                <td class="field-value">${esc(String(v))}</td>
                <td><span class="status-pill ok">found</span></td>
              </tr>
            `).join('')}
            ${missing.map(([k]) => `
              <tr class="missing-row">
                <td class="field-name">${esc(k)}</td>
                <td class="field-value empty">—</td>
                <td><span class="status-pill miss">missing</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
      <div class="result-card">
        <h4>Extraction Details</h4>
        ${statRow('Fields found', d.fields_found)}
        ${statRow('Fields missing', d.fields_missing)}
        ${statRow('Strategy', d.strategy)}
      </div>
      <div class="result-card">
        <h4>Strategies Used</h4>
        <div class="tag-group">
          ${(d.strategies_used || [d.strategy]).map(s => `<span class="tag">${s}</span>`).join('')}
        </div>
      </div>
    </div>
  `;
  showResult(html);
}

function renderSummarize(d) {
  const methodLabel = d.method === 'ai' ? '🤖 AI-powered (Claude)' : '📝 Extractive';
  const compressionRatio = d.original_word_count > 0
    ? Math.round((1 - d.summary.split(/\s+/).length / d.original_word_count) * 100)
    : 0;

  setResultHeader('Summary',
    `${d.method === 'ai' ? 'AI-generated' : 'Extractive'} summary in ${d.format} format`);

  const html = `
    <div class="result-grid">
      <div class="result-card full-width">
        <h4>Summary</h4>
        <div class="summary-text">${formatSummary(d.summary)}</div>
      </div>
      <div class="result-card">
        <h4>Method</h4>
        <div class="method-display">${methodLabel}</div>
        <span class="tag">${d.format}</span>
      </div>
      <div class="result-card">
        <h4>Compression</h4>
        ${statRow('Original words', d.original_word_count)}
        ${statRow('Sentences', d.sentence_count)}
        ${statRow('Reduction', `${compressionRatio}%`)}
      </div>
    </div>
  `;
  showResult(html);
}

function renderPipeline(d) {
  const pipelineName = d.pipeline === 'github' ? 'GitHub Repository Analysis' : 'Post Activity Analysis';

  setResultHeader(pipelineName,
    'TypeScript pipeline completed: Fetch → Clean → Filter → Aggregate → Format');

  // Parse markdown table to HTML
  const tableHtml = markdownTableToHtml(d.output);

  const html = `
    <div class="result-grid">
      <div class="result-card full-width">
        <h4>Pipeline Output</h4>
        ${tableHtml}
      </div>
      <div class="result-card">
        <h4>Pipeline Details</h4>
        ${statRow('Pipeline', d.pipeline)}
        ${statRow('Status', '✓ Success')}
      </div>
      <div class="result-card">
        <h4>Data Source</h4>
        <span class="tag type-tag">${d.pipeline === 'github' ? 'GitHub API (live)' : 'JSONPlaceholder API'}</span>
        <p class="card-note">${d.pipeline === 'github'
          ? 'Fetched real repository data from api.github.com'
          : 'Fetched sample post data from jsonplaceholder.typicode.com'}</p>
      </div>
    </div>
  `;
  showResult(html);
}

// ── Markdown table parser ───────────────────────────────────────────────────

function markdownTableToHtml(md) {
  const lines = md.trim().split('\n').filter(l => l.trim());
  if (lines.length < 2) return `<pre class="raw-output">${esc(md)}</pre>`;

  // Check if it looks like a markdown table
  if (!lines[0].includes('|')) return `<pre class="raw-output">${esc(md)}</pre>`;

  const parseRow = line => line.split('|').map(c => c.trim()).filter(Boolean);

  const headers = parseRow(lines[0]);
  // Skip separator line (line 1)
  const rows = lines.slice(2).map(parseRow);

  return `
    <table class="data-table pipeline-table">
      <thead><tr>${headers.map(h => `<th>${esc(h)}</th>`).join('')}</tr></thead>
      <tbody>${rows.map(r => `<tr>${r.map(c => `<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody>
    </table>
  `;
}

// ── Agent Chat ──────────────────────────────────────────────────────────────

let chatBusy = false;

function handleChatSubmit(e) {
  e.preventDefault();
  const input = document.getElementById('chat-input');
  const message = input.value.trim();
  if (!message || chatBusy) return;

  input.value = '';
  input.style.height = 'auto';
  sendChatMessage(message);
}

function sendChatSuggestion(text) {
  if (chatBusy) return;
  sendChatMessage(text);
}

async function sendChatMessage(message) {
  chatBusy = true;
  const messages = document.getElementById('chat-messages');
  const sendBtn = document.getElementById('chat-send-btn');
  sendBtn.disabled = true;

  // Remove welcome if present
  const welcome = messages.querySelector('.chat-welcome');
  if (welcome) welcome.remove();

  // Add user message
  appendChatMessage('user', message);

  // Add agent message placeholder
  const agentBubble = appendChatMessage('agent', '');
  const textEl = agentBubble.querySelector('.chat-text');
  const metaEl = agentBubble.querySelector('.chat-meta');

  // Show typing indicator
  textEl.innerHTML = '<span class="typing-indicator"><span></span><span></span><span></span></span>';

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    if (!res.ok) {
      textEl.textContent = 'Sorry, something went wrong. Please try again.';
      chatBusy = false;
      sendBtn.disabled = false;
      return;
    }

    // Parse SSE stream
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullText = '';
    let toolCalls = [];

    textEl.textContent = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          var currentEvent = line.slice(7).trim();
        } else if (line.startsWith('data: ') && currentEvent) {
          const data = line.slice(6);

          if (currentEvent === 'text') {
            fullText += data;
            textEl.innerHTML = renderChatMarkdown(fullText);
            scrollChatToBottom();
          } else if (currentEvent === 'tool_call') {
            try {
              const tc = JSON.parse(data);
              toolCalls.push(tc);
              appendToolCard(agentBubble, tc);
              scrollChatToBottom();
            } catch { /* skip malformed */ }
          } else if (currentEvent === 'done') {
            try {
              const meta = JSON.parse(data);
              if (meta.demo_mode) {
                metaEl.textContent = 'Demo mode — connect API key for live agent';
              } else {
                metaEl.textContent = `${meta.iterations} iteration${meta.iterations > 1 ? 's' : ''} · ${meta.tool_calls} tool call${meta.tool_calls !== 1 ? 's' : ''} · ${meta.duration_ms}ms`;
              }
            } catch { /* skip */ }
          } else if (currentEvent === 'error') {
            textEl.textContent = `Error: ${data}`;
          }
          currentEvent = null;
        }
      }
    }

    // Final render with markdown
    if (fullText) {
      textEl.innerHTML = renderChatMarkdown(fullText);
    }

  } catch (err) {
    textEl.textContent = 'Network error — is the server running?';
  }

  chatBusy = false;
  sendBtn.disabled = false;
  scrollChatToBottom();
}

function appendChatMessage(role, text) {
  const messages = document.getElementById('chat-messages');
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble chat-${role}`;

  if (role === 'user') {
    bubble.innerHTML = `<div class="chat-text">${esc(text)}</div>`;
  } else {
    bubble.innerHTML = `
      <div class="chat-agent-header"><span class="agent-avatar">🤖</span> Agent</div>
      <div class="chat-text">${text ? renderChatMarkdown(text) : ''}</div>
      <div class="chat-meta"></div>
    `;
  }

  messages.appendChild(bubble);
  scrollChatToBottom();
  return bubble;
}

function appendToolCard(bubble, tc) {
  const card = document.createElement('div');
  card.className = 'chat-tool-card';
  card.innerHTML = `
    <div class="tool-card-header">
      <span class="tool-card-icon">🔧</span>
      <strong>${esc(tc.tool)}</strong>
      ${tc.duration_ms ? `<span class="tool-card-time">${tc.duration_ms}ms</span>` : ''}
    </div>
    ${tc.result ? `<div class="tool-card-result">${esc(JSON.stringify(tc.result, null, 2).slice(0, 200))}${JSON.stringify(tc.result).length > 200 ? '...' : ''}</div>` : ''}
  `;

  const textEl = bubble.querySelector('.chat-text');
  bubble.insertBefore(card, textEl.nextSibling);
}

function renderChatMarkdown(text) {
  let html = esc(text);
  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Italic
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  // Inline code
  html = html.replace(/`(.+?)`/g, '<code class="inline-code">$1</code>');
  // Line breaks
  html = html.replace(/\n/g, '<br>');
  return html;
}

function scrollChatToBottom() {
  const container = document.getElementById('chat-messages');
  container.scrollTop = container.scrollHeight;
}

// Auto-resize chat input
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('chat-input');
  if (input) {
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    });
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleChatSubmit(e);
      }
    });
  }
});

// Set chat mode badge on health check
function updateChatBadge(apiKeyConfigured) {
  const badge = document.getElementById('chat-mode-badge');
  if (!badge) return;
  if (apiKeyConfigured) {
    badge.textContent = '🟢 Live Agent';
    badge.className = 'chat-mode-badge live';
  } else {
    badge.textContent = '🟡 Demo Mode';
    badge.className = 'chat-mode-badge demo';
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function setResultHeader(title, subtitle) {
  document.getElementById('result-title').textContent = title;
  document.getElementById('result-subtitle').textContent = subtitle;
}

function showResult(html) {
  const area = document.getElementById('result-area');
  document.getElementById('result-content').innerHTML = html;
  area.classList.remove('hidden');
  setTimeout(() => {
    area.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, 100);
}

function hideResult() {
  document.getElementById('result-area').classList.add('hidden');
}

function showError(message) {
  setResultHeader('Error', 'Something went wrong');
  showResult(`<div class="error-message"><span class="error-icon">⚠️</span>${esc(message)}</div>`);
}

function statRow(label, value) {
  return `<div class="stat-row"><span class="stat-label">${label}</span><span class="stat-value">${value}</span></div>`;
}

function formatSummary(text) {
  // Convert bullet points to styled list
  if (text.includes('- ')) {
    const items = text.split('\n').filter(l => l.trim().startsWith('- '));
    return `<ul class="summary-list">${items.map(i =>
      `<li>${renderInlineMarkdown(i.replace(/^- /, ''))}</li>`
    ).join('')}</ul>`;
  }
  return `<p class="summary-paragraph">${renderInlineMarkdown(text)}</p>`;
}

function renderInlineMarkdown(text) {
  let html = esc(text);
  // Bold: **text** or __text__
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
  // Italic: *text* or _text_
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  // Inline code: `text`
  html = html.replace(/`(.+?)`/g, '<code class="inline-code">$1</code>');
  // Links: [text](url)
  html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  return html;
}

function flash(elementId) {
  const el = document.getElementById(elementId);
  el.classList.add('flash');
  el.focus();
  setTimeout(() => el.classList.remove('flash'), 600);
}

function esc(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
