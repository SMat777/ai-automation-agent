// ── Tab navigation ──────────────────────────────────────────────────────────

document.querySelectorAll('.tool-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tool-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tool-panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(`panel-${tab.dataset.tool}`).classList.add('active');
    hideResult();
  });
});

// ── Health check ────────────────────────────────────────────────────────────

async function checkHealth() {
  const bar = document.getElementById('status-bar');
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    if (data.api_key_configured) {
      bar.innerHTML = '<span class="status-ok">● Connected — AI summarization enabled</span>';
    } else {
      bar.innerHTML = '<span class="status-warn">● Running without API key — using extractive summarization</span>';
    }
  } catch {
    bar.innerHTML = '<span class="status-warn">● Could not reach server</span>';
  }
}

checkHealth();

// ── API helpers ─────────────────────────────────────────────────────────────

async function callAPI(endpoint, body, button) {
  button.classList.add('loading');
  button.disabled = true;
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
      showError(err.detail || 'Request failed');
      return null;
    }

    const data = await res.json();
    document.getElementById('result-meta').textContent = `${elapsed}ms`;
    return data;
  } catch (err) {
    showError(`Network error: ${err.message}`);
    return null;
  } finally {
    button.classList.remove('loading');
    button.disabled = false;
  }
}

// ── Tool runners ────────────────────────────────────────────────────────────

async function runAnalyze() {
  const text = document.getElementById('analyze-text').value.trim();
  if (!text) return;

  const btn = document.querySelector('#panel-analyze .btn-run');
  const data = await callAPI('analyze', {
    text,
    focus: document.getElementById('analyze-focus').value,
  }, btn);

  if (data) renderAnalyze(data.data);
}

async function runExtract() {
  const text = document.getElementById('extract-text').value.trim();
  const fieldsStr = document.getElementById('extract-fields').value.trim();
  if (!text || !fieldsStr) return;

  const fields = fieldsStr.split(',').map(f => f.trim()).filter(Boolean);
  const btn = document.querySelector('#panel-extract .btn-run');
  const data = await callAPI('extract', {
    text,
    fields,
    strategy: document.getElementById('extract-strategy').value,
  }, btn);

  if (data) renderExtract(data.data);
}

async function runSummarize() {
  const text = document.getElementById('summarize-text').value.trim();
  if (!text) return;

  const btn = document.querySelector('#panel-summarize .btn-run');
  const data = await callAPI('summarize', {
    text,
    format: document.getElementById('summarize-format').value,
    max_points: parseInt(document.getElementById('summarize-points').value),
  }, btn);

  if (data) renderSummarize(data.data);
}

async function runPipeline() {
  const pipeline = document.getElementById('pipeline-select').value;
  const btn = document.querySelector('#panel-pipeline .btn-run');
  const data = await callAPI('pipeline', {
    task: `Run ${pipeline} pipeline`,
    pipeline,
  }, btn);

  if (data) renderPipeline(data.data);
}

// ── Renderers ───────────────────────────────────────────────────────────────

function renderAnalyze(d) {
  const entities = d.entities;
  const allEntities = [
    ...entities.emails.map(e => `📧 ${e}`),
    ...entities.dates.map(e => `📅 ${e}`),
    ...entities.urls.map(e => `🔗 ${e}`),
    ...entities.organizations.map(e => `🏢 ${e}`),
  ];

  const html = `
    <div class="result-grid">
      <div class="result-card">
        <h4>Document Type</h4>
        <span class="tag type-tag">${d.document_type.replace(/_/g, ' ')}</span>
      </div>
      <div class="result-card">
        <h4>Statistics</h4>
        <div class="stat-row"><span class="label">Words</span><span class="value">${d.statistics.word_count}</span></div>
        <div class="stat-row"><span class="label">Sentences</span><span class="value">${d.statistics.sentence_count}</span></div>
        <div class="stat-row"><span class="label">Paragraphs</span><span class="value">${d.statistics.paragraph_count}</span></div>
      </div>
      <div class="result-card">
        <h4>Entities Found</h4>
        ${allEntities.length > 0
          ? `<ul class="entity-list">${allEntities.map(e => `<li>${escapeHtml(e)}</li>`).join('')}</ul>`
          : '<p style="color:var(--text-muted);font-size:0.85rem">No entities detected</p>'}
      </div>
      <div class="result-card">
        <h4>Sections</h4>
        ${d.sections.length > 0
          ? `<ul class="entity-list">${d.sections.map(s => `<li>${'─'.repeat(s.level)} ${escapeHtml(s.title)}</li>`).join('')}</ul>`
          : '<p style="color:var(--text-muted);font-size:0.85rem">No headings detected</p>'}
      </div>
      ${d.key_points.length > 0 ? `
        <div class="result-card full-width">
          <h4>Key Points</h4>
          ${d.key_points.map(p => `<div class="key-point">${escapeHtml(p)}</div>`).join('')}
        </div>
      ` : ''}
    </div>
  `;
  showResult(html);
}

function renderExtract(d) {
  const rows = Object.entries(d.extracted).map(([k, v]) => `
    <tr>
      <td><strong>${escapeHtml(k)}</strong></td>
      <td>${v !== null ? escapeHtml(String(v)) : '<span style="color:var(--text-muted)">not found</span>'}</td>
    </tr>
  `).join('');

  const html = `
    <div class="result-grid">
      <div class="result-card full-width">
        <h4>Extracted Data</h4>
        <table class="extracted-table">
          <thead><tr><th>Field</th><th>Value</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      <div class="result-card">
        <h4>Stats</h4>
        <div class="stat-row"><span class="label">Fields found</span><span class="value">${d.fields_found}</span></div>
        <div class="stat-row"><span class="label">Fields missing</span><span class="value">${d.fields_missing}</span></div>
      </div>
      <div class="result-card">
        <h4>Strategy</h4>
        <span class="tag">${d.strategy}</span>
        ${d.strategies_used ? d.strategies_used.map(s => `<span class="tag">${s}</span>`).join('') : ''}
      </div>
    </div>
  `;
  showResult(html);
}

function renderSummarize(d) {
  const html = `
    <div class="result-grid">
      <div class="result-card full-width">
        <h4>Summary</h4>
        <div class="summary-text">${escapeHtml(d.summary)}</div>
      </div>
      <div class="result-card">
        <h4>Method</h4>
        <span class="tag method-tag">${d.method}</span>
        <span class="tag">${d.format}</span>
      </div>
      <div class="result-card">
        <h4>Stats</h4>
        <div class="stat-row"><span class="label">Original words</span><span class="value">${d.original_word_count}</span></div>
        <div class="stat-row"><span class="label">Sentences</span><span class="value">${d.sentence_count}</span></div>
      </div>
    </div>
  `;
  showResult(html);
}

function renderPipeline(d) {
  const html = `
    <div class="result-grid">
      <div class="result-card full-width">
        <h4>Pipeline Output</h4>
        <div class="pipeline-output">${escapeHtml(d.output)}</div>
      </div>
      <div class="result-card">
        <h4>Details</h4>
        <div class="stat-row"><span class="label">Pipeline</span><span class="value">${d.pipeline}</span></div>
        <div class="stat-row"><span class="label">Task</span><span class="value">${escapeHtml(d.task)}</span></div>
      </div>
      <div class="result-card">
        <h4>Status</h4>
        <span class="tag type-tag">✓ success</span>
      </div>
    </div>
  `;
  showResult(html);
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function showResult(html) {
  const area = document.getElementById('result-area');
  document.getElementById('result-content').innerHTML = html;
  area.classList.remove('hidden');
  area.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideResult() {
  document.getElementById('result-area').classList.add('hidden');
}

function showError(message) {
  showResult(`<div class="error-message">${escapeHtml(message)}</div>`);
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
