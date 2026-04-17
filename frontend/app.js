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
  } catch {
    bar.innerHTML = '<span class="status-dot err"></span> Server not reachable';
  }
}

checkHealth();

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

// ── API call ────────────────────────────────────────────────────────────────

async function callAPI(endpoint, body, tool) {
  showLoading(tool);
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
      showError(err.detail || `Request failed (${res.status})`);
      return null;
    }

    const data = await res.json();
    hideLoading();
    document.getElementById('result-time').textContent = `${elapsed}ms`;
    return data;
  } catch (err) {
    hideLoading();
    showError(`Network error: ${err.message}`);
    return null;
  }
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
    area.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
      `<li>${esc(i.replace(/^- /, ''))}</li>`
    ).join('')}</ul>`;
  }
  return `<p class="summary-paragraph">${esc(text)}</p>`;
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
