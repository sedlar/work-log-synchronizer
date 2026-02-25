// ABOUTME: Tampermonkey userscript that imports Clockify-exported time entries into BambooHR timesheets.
// ABOUTME: Provides a floating UI panel for pasting JSON, previewing entries with conflict detection, and POSTing to BambooHR.

// ==UserScript==
// @name         BambooHR Clockify Import
// @namespace    clockify-bamboo-sync
// @version      1.0
// @description  Import time entries from Clockify export into BambooHR timesheet
// @match        https://*.bamboohr.com/employees/timesheet*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  // --- Page data extraction ---

  function getTimesheetData() {
    const el = document.getElementById('js-timesheet-data');
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch {
      return null;
    }
  }

  function getEmployeeId(data) {
    return data?.employeeId ?? null;
  }

  function getCsrfToken() {
    const scripts = document.querySelectorAll('script');
    for (const script of scripts) {
      const match = script.textContent.match(/CSRF_TOKEN\s*=\s*"([^"]+)"/);
      if (match) return match[1];
    }
    return null;
  }

  function getTimesheetDates(data) {
    const details = data?.timesheet?.dailyDetails;
    if (!details) return [];
    return Object.keys(details).sort();
  }

  function getExistingEntries(data, date) {
    const day = data?.timesheet?.dailyDetails?.[date];
    if (!day) return [];
    return [...(day.hourEntries || []), ...(day.clockEntries || [])];
  }

  function getProjectsWithTasks(data) {
    const pwt = data?.projectsWithTasks;
    if (!pwt) return {};
    const byId = pwt.byId;
    // byId can be [] (empty array) or {} (object)
    if (Array.isArray(byId) && byId.length === 0) return {};
    return byId || {};
  }

  function getProjectName(projects, projectId) {
    const p = projects[String(projectId)];
    return p ? p.name : null;
  }

  function getTaskName(projects, projectId, taskId) {
    if (taskId == null) return null;
    const p = projects[String(projectId)];
    if (!p) return null;
    const tasks = p.tasks?.byId;
    if (Array.isArray(tasks)) return null;
    const t = tasks?.[String(taskId)];
    return t ? t.name : null;
  }

  // --- Validation ---

  function timeToMinutes(timeStr) {
    const [h, m] = timeStr.split(':').map(Number);
    return h * 60 + m;
  }

  function rangesOverlap(s1, e1, s2, e2) {
    return s1 < e2 && s2 < e1;
  }

  function validateEntry(entry, timesheetDates, projects, data) {
    const errors = [];
    const warnings = [];

    // Check date in timesheet period
    if (!timesheetDates.includes(entry.date)) {
      errors.push('Date outside timesheet period');
    }

    // Check start < end
    if (entry.start >= entry.end) {
      errors.push('Start time must be before end time');
    }

    // Check project exists
    const project = projects[String(entry.projectId)];
    if (!project) {
      errors.push(`Unknown project ID ${entry.projectId}`);
    } else if (entry.taskId != null) {
      // Check task exists under project
      const tasks = project.tasks?.byId;
      const taskExists = !Array.isArray(tasks) && tasks?.[String(entry.taskId)];
      if (!taskExists) {
        errors.push(`Unknown task ID ${entry.taskId} for project ${project.name}`);
      }
    }

    // Check overlaps with existing entries
    if (errors.length === 0) {
      const existing = getExistingEntries(data, entry.date);
      const entryStart = timeToMinutes(entry.start);
      const entryEnd = timeToMinutes(entry.end);

      for (const ex of existing) {
        // hourEntries have hours but no start/end - can't check overlap precisely
        // clockEntries have start/end
        if (ex.start && ex.end) {
          const exStart = timeToMinutes(ex.start);
          const exEnd = timeToMinutes(ex.end);
          if (rangesOverlap(entryStart, entryEnd, exStart, exEnd)) {
            warnings.push('Overlaps with existing entry');
            break;
          }
        }
      }

      // If there are hourEntries (no start/end), warn if the date already has entries
      const day = data?.timesheet?.dailyDetails?.[entry.date];
      if (day && day.hourEntries?.length > 0) {
        warnings.push('Date already has hour entries');
      }
    }

    if (errors.length > 0) return { status: 'invalid', icon: '\u274C', messages: errors };
    if (warnings.length > 0) return { status: 'warning', icon: '\u26A0\uFE0F', messages: warnings };
    return { status: 'ready', icon: '\u2705', messages: ['Ready'] };
  }

  // --- UI creation ---

  function createStyles() {
    const style = document.createElement('style');
    style.textContent = `
      #clockify-import-panel {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 400px;
        max-height: 80vh;
        background: #fff;
        border: 1px solid #ccc;
        border-radius: 8px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 13px;
        z-index: 99999;
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }
      #clockify-import-panel.minimized {
        max-height: none;
        height: auto;
      }
      #clockify-import-panel.minimized .ci-body {
        display: none;
      }
      .ci-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 14px;
        background: #2d3748;
        color: #fff;
        cursor: pointer;
        user-select: none;
        flex-shrink: 0;
      }
      .ci-header-title {
        font-weight: 600;
        font-size: 14px;
      }
      .ci-header-toggle {
        font-size: 12px;
        opacity: 0.8;
      }
      .ci-body {
        padding: 12px 14px;
        overflow-y: auto;
        flex: 1;
      }
      .ci-textarea {
        width: 100%;
        height: 80px;
        border: 1px solid #d1d5db;
        border-radius: 4px;
        padding: 8px;
        font-size: 12px;
        font-family: monospace;
        resize: vertical;
        box-sizing: border-box;
      }
      .ci-textarea:focus {
        outline: none;
        border-color: #3b82f6;
        box-shadow: 0 0 0 2px rgba(59,130,246,0.2);
      }
      .ci-btn {
        padding: 6px 14px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 13px;
        font-weight: 500;
        margin-right: 6px;
        margin-top: 8px;
      }
      .ci-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      .ci-btn-primary {
        background: #3b82f6;
        color: #fff;
      }
      .ci-btn-primary:hover:not(:disabled) {
        background: #2563eb;
      }
      .ci-btn-warning {
        background: #f59e0b;
        color: #fff;
      }
      .ci-btn-warning:hover:not(:disabled) {
        background: #d97706;
      }
      .ci-btn-secondary {
        background: #e5e7eb;
        color: #374151;
      }
      .ci-btn-secondary:hover:not(:disabled) {
        background: #d1d5db;
      }
      .ci-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        font-size: 12px;
      }
      .ci-table th {
        background: #f3f4f6;
        padding: 6px 8px;
        text-align: left;
        font-weight: 600;
        border-bottom: 1px solid #d1d5db;
      }
      .ci-table td {
        padding: 5px 8px;
        border-bottom: 1px solid #e5e7eb;
        vertical-align: top;
      }
      .ci-table tr:hover {
        background: #f9fafb;
      }
      .ci-summary {
        margin-top: 10px;
        padding: 8px;
        background: #f3f4f6;
        border-radius: 4px;
        font-size: 12px;
      }
      .ci-error {
        color: #dc2626;
        margin-top: 8px;
        font-size: 12px;
      }
      .ci-success {
        color: #16a34a;
        margin-top: 8px;
        font-size: 12px;
      }
      .ci-status-invalid { color: #dc2626; }
      .ci-status-warning { color: #d97706; }
      .ci-status-ready { color: #16a34a; }
      .ci-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
      }
    `;
    document.head.appendChild(style);
  }

  function createPanel() {
    const panel = document.createElement('div');
    panel.id = 'clockify-import-panel';
    panel.innerHTML = `
      <div class="ci-header">
        <span class="ci-header-title">Clockify Import</span>
        <span class="ci-header-toggle">\u25BC</span>
      </div>
      <div class="ci-body">
        <textarea class="ci-textarea" placeholder="Paste exported JSON here..."></textarea>
        <div class="ci-actions">
          <button class="ci-btn ci-btn-primary ci-btn-preview">Preview</button>
          <button class="ci-btn ci-btn-secondary ci-btn-clear">Clear</button>
        </div>
        <div class="ci-preview-area"></div>
      </div>
    `;
    document.body.appendChild(panel);
    return panel;
  }

  // --- Preview logic ---

  function renderPreview(entries, validations, projects) {
    const readyCount = validations.filter(v => v.status === 'ready').length;
    const warnCount = validations.filter(v => v.status === 'warning').length;
    const invalidCount = validations.filter(v => v.status === 'invalid').length;

    let html = '<table class="ci-table"><thead><tr>';
    html += '<th>Date</th><th>Time</th><th>Project</th><th>Status</th>';
    html += '</tr></thead><tbody>';

    for (let i = 0; i < entries.length; i++) {
      const e = entries[i];
      const v = validations[i];
      const projName = getProjectName(projects, e.projectId) || `#${e.projectId}`;
      const taskName = getTaskName(projects, e.projectId, e.taskId);
      const projDisplay = taskName ? `${projName} / ${taskName}` : projName;
      const datePart = e.date.substring(5); // MM-DD

      html += `<tr>`;
      html += `<td>${datePart}</td>`;
      html += `<td>${e.start}-${e.end}</td>`;
      html += `<td title="${e.note || ''}">${projDisplay}</td>`;
      html += `<td class="ci-status-${v.status}" title="${v.messages.join(', ')}">${v.icon}</td>`;
      html += `</tr>`;
    }

    html += '</tbody></table>';
    html += `<div class="ci-summary">${entries.length} entries (${readyCount} ready`;
    if (warnCount > 0) html += `, ${warnCount} warning`;
    if (invalidCount > 0) html += `, ${invalidCount} invalid`;
    html += ')</div>';

    html += '<div class="ci-actions">';
    if (readyCount > 0) {
      html += `<button class="ci-btn ci-btn-primary ci-btn-import-ready">Import ${readyCount} ready</button>`;
    }
    if (warnCount > 0) {
      const importAllCount = readyCount + warnCount;
      html += `<button class="ci-btn ci-btn-warning ci-btn-import-all">Import all ${importAllCount}</button>`;
    }
    html += '</div>';
    html += '<div class="ci-result-area"></div>';

    return html;
  }

  // --- Import logic ---

  async function importEntries(entries, employeeId, csrfToken) {
    const body = {
      entries: entries.map((e, i) => ({
        id: null,
        trackingId: i + 1,
        employeeId: employeeId,
        date: e.date,
        start: e.start,
        end: e.end,
        note: e.note || '',
        projectId: e.projectId,
        taskId: e.taskId ?? null,
      })),
    };

    const response = await fetch('/timesheet/clock/entries', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Csrf-Token': csrfToken,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`HTTP ${response.status}: ${text}`);
    }

    return response.json();
  }

  // --- Init ---

  function init() {
    const pageData = getTimesheetData();
    if (!pageData) {
      console.warn('[Clockify Import] Could not find #js-timesheet-data on this page');
      return;
    }

    const employeeId = getEmployeeId(pageData);
    const csrfToken = getCsrfToken();
    const timesheetDates = getTimesheetDates(pageData);
    const projects = getProjectsWithTasks(pageData);

    if (!employeeId || !csrfToken) {
      console.warn('[Clockify Import] Missing employeeId or CSRF token');
      return;
    }

    createStyles();
    const panel = createPanel();
    const header = panel.querySelector('.ci-header');
    const toggle = panel.querySelector('.ci-header-toggle');
    const textarea = panel.querySelector('.ci-textarea');
    const previewArea = panel.querySelector('.ci-preview-area');
    const btnPreview = panel.querySelector('.ci-btn-preview');
    const btnClear = panel.querySelector('.ci-btn-clear');

    let parsedEntries = [];
    let validationResults = [];

    // Minimize/maximize
    header.addEventListener('click', () => {
      panel.classList.toggle('minimized');
      toggle.textContent = panel.classList.contains('minimized') ? '\u25B2' : '\u25BC';
    });

    // Clear
    btnClear.addEventListener('click', () => {
      textarea.value = '';
      previewArea.innerHTML = '';
      parsedEntries = [];
      validationResults = [];
    });

    // Preview
    btnPreview.addEventListener('click', () => {
      previewArea.innerHTML = '';
      let json;
      try {
        json = JSON.parse(textarea.value);
      } catch {
        previewArea.innerHTML = '<div class="ci-error">Invalid JSON</div>';
        return;
      }

      const entries = json.entries;
      if (!Array.isArray(entries) || entries.length === 0) {
        previewArea.innerHTML = '<div class="ci-error">No entries found in JSON</div>';
        return;
      }

      parsedEntries = entries;
      validationResults = entries.map(e => validateEntry(e, timesheetDates, projects, pageData));

      previewArea.innerHTML = renderPreview(entries, validationResults, projects);

      // Bind import buttons
      const btnImportReady = previewArea.querySelector('.ci-btn-import-ready');
      const btnImportAll = previewArea.querySelector('.ci-btn-import-all');
      const resultArea = previewArea.querySelector('.ci-result-area');

      async function doImport(includeWarnings) {
        const toImport = parsedEntries.filter((_, i) => {
          const s = validationResults[i].status;
          return s === 'ready' || (includeWarnings && s === 'warning');
        });

        if (toImport.length === 0) {
          resultArea.innerHTML = '<div class="ci-error">No entries to import</div>';
          return;
        }

        // Disable buttons during import
        if (btnImportReady) btnImportReady.disabled = true;
        if (btnImportAll) btnImportAll.disabled = true;
        resultArea.innerHTML = '<div>Importing...</div>';

        try {
          await importEntries(toImport, employeeId, csrfToken);
          resultArea.innerHTML = `<div class="ci-success">Imported ${toImport.length} entries. Reloading...</div>`;
          setTimeout(() => location.reload(), 1500);
        } catch (err) {
          resultArea.innerHTML = `<div class="ci-error">Import failed: ${err.message}</div>`;
          if (btnImportReady) btnImportReady.disabled = false;
          if (btnImportAll) btnImportAll.disabled = false;
        }
      }

      if (btnImportReady) {
        btnImportReady.addEventListener('click', () => doImport(false));
      }
      if (btnImportAll) {
        btnImportAll.addEventListener('click', () => doImport(true));
      }
    });
  }

  init();
})();
