/* Scenario result renderer — turns structured API payloads into product UI cards. */

function renderScenarioResult(payload) {
  if (!payload || typeof payload !== 'object') {
    return '<div class="chat-msg assistant">No scenario output available.</div>';
  }

  const outputType = payload.output_type;
  const result = payload.result || {};

  if (outputType === 'invoice_result') {
    return renderInvoiceResult(payload.scenario_name, result);
  }
  if (outputType === 'email_triage_result') {
    return renderEmailTriageResult(payload.scenario_name, result);
  }
  if (outputType === 'contract_review_result') {
    return renderContractReviewResult(payload.scenario_name, result);
  }

  return `<pre>${escapeHtml(JSON.stringify(payload, null, 2))}</pre>`;
}

function renderInvoiceResult(scenarioName, result) {
  const erp = result.erp_output || {};
  const extracted = erp.extracted_fields || {};
  const entities = erp.entities || {};
  const issues = getValidationIssues(result);

  return `
    <div class="scenario-result">
      <div class="result-header">
        <h3>${escapeHtml(scenarioName || 'Invoice Result')}</h3>
        <span class="status-pill ${result.validation_errors > 0 ? 'warn' : 'ok'}">
          ${result.validation_errors > 0 ? 'Validation warnings' : 'Validated'}
        </span>
      </div>

      <div class="result-grid two-col">
        <div class="result-card">
          <h4>Extracted Fields</h4>
          ${renderKeyValueList(extracted)}
        </div>
        <div class="result-card">
          <h4>Validation</h4>
          <div class="metric-row"><span>Confidence</span><strong>${formatPercent(result.confidence)}</strong></div>
          <div class="metric-row"><span>Errors</span><strong>${result.validation_errors ?? 0}</strong></div>
          <div class="metric-row"><span>Fields</span><strong>${escapeHtml(result.fields_extracted || '-')}</strong></div>
          ${issues.length ? `<ul class="issue-list">${issues.map(i => `<li>${escapeHtml(i)}</li>`).join('')}</ul>` : '<p class="muted">No validation issues.</p>'}
        </div>
      </div>

      <div class="result-card">
        <h4>ERP Payload</h4>
        <pre>${escapeHtml(JSON.stringify(erp, null, 2))}</pre>
      </div>

      ${Object.keys(entities).length ? `<div class="result-card"><h4>Entities</h4>${renderEntityBadges(entities)}</div>` : ''}
    </div>
  `;
}

function renderEmailTriageResult(scenarioName, result) {
  const classification = result.classification || {};
  const lookup = result.order_lookup || {};
  const draft = result.reply_draft || {};

  return `
    <div class="scenario-result">
      <div class="result-header">
        <h3>${escapeHtml(scenarioName || 'Email Triage')}</h3>
        <span class="status-pill ${classification.priority === 'high' ? 'warn' : 'ok'}">${escapeHtml(classification.priority || 'unknown')} priority</span>
      </div>

      <div class="result-grid two-col">
        <div class="result-card">
          <h4>Classification</h4>
          <div class="metric-row"><span>Category</span><strong>${escapeHtml(classification.category || '-')}</strong></div>
          <div class="metric-row"><span>Intent</span><strong>${escapeHtml(classification.intent || '-')}</strong></div>
          <div class="metric-row"><span>Priority</span><strong>${escapeHtml(classification.priority || '-')}</strong></div>
          ${classification.entities ? renderEntityBadges(classification.entities) : ''}
        </div>

        <div class="result-card">
          <h4>Order Lookup</h4>
          <div class="metric-row"><span>Status</span><strong>${escapeHtml(lookup.status || 'not_run')}</strong></div>
          ${lookup.order ? `<pre>${escapeHtml(JSON.stringify(lookup.order, null, 2))}</pre>` : `<p class="muted">${escapeHtml(lookup.message || 'No order details available.')}</p>`}
        </div>
      </div>

      <div class="result-card">
        <h4>Draft Reply (Human review required)</h4>
        <div class="draft-box">${renderMarkdown(draft.draft || 'No draft generated.')}</div>
      </div>
    </div>
  `;
}

function renderContractReviewResult(scenarioName, result) {
  const erp = result.erp_output || {};
  const extracted = erp.extracted_fields || {};
  const issues = getValidationIssues(result);

  return `
    <div class="scenario-result">
      <div class="result-header">
        <h3>${escapeHtml(scenarioName || 'Contract Review')}</h3>
        <span class="status-pill ${issues.length ? 'warn' : 'ok'}">${issues.length ? 'Risks flagged' : 'No major risks'}</span>
      </div>

      <div class="result-grid two-col">
        <div class="result-card">
          <h4>Key Terms</h4>
          ${renderKeyValueList(extracted)}
        </div>
        <div class="result-card">
          <h4>Risk & Validation</h4>
          <div class="metric-row"><span>Confidence</span><strong>${formatPercent(result.confidence)}</strong></div>
          <div class="metric-row"><span>Validation issues</span><strong>${issues.length}</strong></div>
          ${issues.length ? `<ul class="issue-list">${issues.map(i => `<li>${escapeHtml(i)}</li>`).join('')}</ul>` : '<p class="muted">No issues detected.</p>'}
        </div>
      </div>

      <div class="result-card">
        <h4>Structured Output</h4>
        <pre>${escapeHtml(JSON.stringify(erp, null, 2))}</pre>
      </div>
    </div>
  `;
}

function getValidationIssues(result) {
  const steps = result.steps || [];
  const validateStep = steps.find(s => s.name === 'validate');
  const issues = validateStep?.data?.issues || [];
  return issues.map(i => i.message).filter(Boolean);
}

function renderKeyValueList(obj) {
  const entries = Object.entries(obj || {});
  if (!entries.length) return '<p class="muted">No extracted fields.</p>';
  return `<div class="kv-list">${entries.map(([k, v]) => `<div class="kv-item"><span>${escapeHtml(k)}</span><strong>${escapeHtml(String(v))}</strong></div>`).join('')}</div>`;
}

function renderEntityBadges(entities) {
  const rows = Object.entries(entities || {}).filter(([, values]) => Array.isArray(values) && values.length > 0);
  if (!rows.length) return '<p class="muted">No entities detected.</p>';

  return rows
    .map(([group, values]) => `
      <div class="entity-group">
        <label>${escapeHtml(group)}</label>
        <div class="entity-badges">
          ${values.map(v => `<span class="entity-badge">${escapeHtml(String(v))}</span>`).join('')}
        </div>
      </div>
    `)
    .join('');
}

function formatPercent(value) {
  if (typeof value !== 'number') return '-';
  return `${Math.round(value * 100)}%`;
}
