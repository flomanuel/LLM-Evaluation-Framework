const DEFAULT_API_BASE = "http://127.0.0.1:8000/api/v1";

const state = {
    apiBase: localStorage.getItem("apiBase") || DEFAULT_API_BASE,
    runs: {page: 0, size: 10, totalPages: 0},
    testCases: {page: 0, size: 10, totalPages: 0},
    selectedRunId: null,
    runEtag: null,
    analysisEtags: new Map(),
    statusPollTimer: null,
};

class ApiError extends Error {
    constructor(status, message) {
        super(message);
        this.status = status;
    }
}

function getApiBase() {
    return state.apiBase.replace(/\/+$/, "");
}

async function apiFetch(path, options = {}) {
    const url = getApiBase() + path;
    let response;
    try {
        response = await fetch(url, options);
    } catch (err) {
        throw new ApiError(0, `Could not reach ${url}. Check the API base URL and the API's CORS_ALLOW_ORIGINS setting.`);
    }
    const contentType = response.headers.get("content-type") || "";
    let data = null;
    if (contentType.includes("application/json")) {
        data = await response.json();
    } else if (contentType.includes("application/zip")) {
        data = await response.blob();
    }
    return {response, data};
}

function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value).replace(/[&<>"']/g, (c) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
}

function formatDateTime(value) {
    if (!value) return "—";
    let iso = value.includes("T") ? value : value.replace(" ", "T");
    iso = iso.replace(/(\.\d{3})\d+/, "$1");
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
}

function shortId(id) {
    if (!id) return "";
    return id.length > 12 ? `${id.slice(0, 8)}…` : id;
}

function statusBadgeClass(status) {
    switch (status) {
        case "completed":
            return "badge-success";
        case "failed":
            return "badge-danger";
        case "running":
            return "badge-warning";
        default:
            return "badge-neutral";
    }
}

function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = message;
    container.appendChild(el);
    setTimeout(() => el.remove(), 6000);
}

function openModal(html) {
    document.getElementById("modal-content").innerHTML = html;
    document.getElementById("modal-backdrop").classList.remove("hidden");
}

function closeModal() {
    document.getElementById("modal-backdrop").classList.add("hidden");
    document.getElementById("modal-content").innerHTML = "";
}

function spinnerHtml(label) {
    return `<span class="loading-inline"><span class="spinner"></span>${label ? escapeHtml(label) : ""}</span>`;
}

function renderTableLoading(selector, colspan, label) {
    const tbody = document.querySelector(selector);
    if (tbody) tbody.innerHTML = `<tr class="loading-row"><td colspan="${colspan}">${spinnerHtml(label || "Loading…")}</td></tr>`;
}

function beginButtonLoading(button, loadingText) {
    if (!button) return () => {};
    const original = button.innerHTML;
    button.disabled = true;
    button.classList.add("is-loading");
    button.innerHTML = `<span class="spinner"></span> ${escapeHtml(loadingText)}`;
    return () => {
        button.disabled = false;
        button.classList.remove("is-loading");
        button.innerHTML = original;
    };
}

function rawJsonBlock(data) {
    return `
    <details class="raw-json">
      <summary>Show raw JSON</summary>
      <pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>
    </details>
  `;
}

function renderPagination(containerId, page, size, totalElements, totalPages, onChange) {
    const el = document.getElementById(containerId);
    el.innerHTML = `
    <button class="small" id="${containerId}-prev" ${page <= 0 ? "disabled" : ""}>&larr; Prev</button>
    <span>Page ${page + 1} / ${Math.max(totalPages, 1)} (${totalElements} total)</span>
    <button class="small" id="${containerId}-next" ${page + 1 >= totalPages ? "disabled" : ""}>Next &rarr;</button>
  `;
    const prevBtn = document.getElementById(`${containerId}-prev`);
    const nextBtn = document.getElementById(`${containerId}-next`);
    if (prevBtn) prevBtn.addEventListener("click", () => onChange(page - 1));
    if (nextBtn) nextBtn.addEventListener("click", () => onChange(page + 1));
}

async function checkHealth() {
    const liveDot = document.getElementById("liveness-dot");
    const readyDot = document.getElementById("readiness-dot");
    try {
        const {response} = await apiFetch("/health/liveness");
        liveDot.classList.toggle("ok", response.ok);
        liveDot.classList.toggle("fail", !response.ok);
        liveDot.title = response.ok ? "Liveness: up" : `Liveness: HTTP ${response.status}`;
    } catch (err) {
        liveDot.classList.remove("ok");
        liveDot.classList.add("fail");
        liveDot.title = err.message;
    }
    try {
        const {response, data} = await apiFetch("/health/readiness");
        const dbUp = response.ok && data && data.db === "up";
        readyDot.classList.toggle("ok", dbUp);
        readyDot.classList.toggle("fail", !dbUp);
        readyDot.title = data ? `Readiness: db=${data.db}` : `Readiness: HTTP ${response.status}`;
    } catch (err) {
        readyDot.classList.remove("ok");
        readyDot.classList.add("fail");
        readyDot.title = err.message;
    }
}

async function startRun() {
    const done = beginButtonLoading(document.getElementById("start-run-btn"), "Starting…");
    const resultsDir = document.getElementById("results-dir-input").value.trim();
    const body = resultsDir ? JSON.stringify({results_dir: resultsDir}) : undefined;
    const box = document.getElementById("start-run-result");
    box.classList.remove("hidden", "error");
    box.innerHTML = spinnerHtml("Starting…");
    try {
        const {response} = await apiFetch("/test-runs", {
            method: "POST",
            headers: body ? {"Content-Type": "application/json"} : {},
            body,
        });
        if (response.status === 202) {
            const location = response.headers.get("Location") || "";
            const etag = response.headers.get("ETag") || "";
            const runId = location.split("/").filter(Boolean).pop();
            box.innerHTML = `Started. <code>run_id=${escapeHtml(runId || "?")}</code>, ETag=${escapeHtml(etag)}. ` +
                `<button class="small" id="view-started-run-btn">View run</button>`;
            const viewBtn = document.getElementById("view-started-run-btn");
            if (viewBtn && runId) viewBtn.addEventListener("click", () => selectRun(runId));
            showToast("Run started", "success");
            await loadRuns();
        } else if (response.status === 409) {
            box.classList.add("error");
            box.textContent = "409 Conflict — a run is already pending or running.";
        } else {
            box.classList.add("error");
            box.textContent = `Unexpected response: HTTP ${response.status}`;
        }
    } catch (err) {
        box.classList.add("error");
        box.textContent = err.message;
    } finally {
        done();
    }
}

async function loadRuns() {
    const status = document.getElementById("filter-status").value;
    const startAfter = document.getElementById("filter-start-after").value;
    const startBefore = document.getElementById("filter-start-before").value;
    const size = parseInt(document.getElementById("filter-size").value, 10) || 10;
    state.runs.size = size;

    const params = new URLSearchParams();
    params.set("page", String(state.runs.page));
    params.set("size", String(size));
    if (status) params.set("status", status);
    if (startAfter) params.set("start_after", startAfter);
    if (startBefore) params.set("start_before", startBefore);

    renderTableLoading("#runs-table tbody", 6, "Loading runs…");
    try {
        const {response, data} = await apiFetch(`/test-runs?${params.toString()}`);
        if (!response.ok) {
            showToast(`Failed to load runs: HTTP ${response.status}`, "error");
            return;
        }
        renderRunsTable(data.content || []);
        state.runs.totalPages = data.page.total_pages;
        renderPagination("runs-pagination", data.page.number, data.page.size, data.page.total_elements, data.page.total_pages, (p) => {
            state.runs.page = p;
            loadRuns();
        });
    } catch (err) {
        showToast(err.message, "error");
    }
}

function renderRunsTable(runs) {
    const tbody = document.querySelector("#runs-table tbody");
    if (!runs.length) {
        tbody.innerHTML = `<tr><td colspan="6" class="muted">No runs found.</td></tr>`;
        return;
    }
    tbody.innerHTML = runs.map((run) => `
    <tr>
      <td><code title="${escapeHtml(run.run_id)}">${escapeHtml(shortId(run.run_id))}</code></td>
      <td><span class="badge ${statusBadgeClass(run.status)}">${escapeHtml(run.status || "unknown")}</span></td>
      <td>${formatDateTime(run.start_ts)}</td>
      <td>${formatDateTime(run.end_ts)}</td>
      <td>${run.version ?? "—"}</td>
      <td><button class="small view-run-btn" data-run-id="${escapeHtml(run.run_id)}">View</button></td>
    </tr>
  `).join("");
    tbody.querySelectorAll(".view-run-btn").forEach((btn) => {
        btn.addEventListener("click", () => selectRun(btn.dataset.runId));
    });
}

function selectRun(runId) {
    state.selectedRunId = runId;
    state.runEtag = null;
    state.analysisEtags.clear();
    stopStatusPolling();
    document.getElementById("run-detail-card").classList.remove("hidden");
    document.getElementById("detail-run-id").textContent = runId;
    document.getElementById("etag-indicator").textContent = "";
    document.getElementById("status-poll-log").innerHTML = "";
    document.getElementById("overview-content").innerHTML = `<div class="overview-loading">${spinnerHtml("Loading run…")}</div>`;
    renderTableLoading("#test-cases-table tbody", 7, "Loading test cases…");
    renderTableLoading("#analyses-table tbody", 6, "Loading analyses…");
    switchTab("overview");
    loadOverview();
    state.testCases.page = 0;
    loadTestCases();
    loadAnalyses();
    document.getElementById("run-detail-card").scrollIntoView({behavior: "smooth", block: "start"});
}

function closeDetail() {
    stopStatusPolling();
    state.selectedRunId = null;
    document.getElementById("run-detail-card").classList.add("hidden");
}

function switchTab(tab) {
    document.querySelectorAll(".tab-btn").forEach((btn) => btn.classList.toggle("active", btn.dataset.tab === tab));
    document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.toggle("hidden", panel.id !== `tab-${tab}`));
}

async function loadOverview(useEtag = false) {
    if (!state.selectedRunId) return;
    const headers = {};
    if (useEtag && state.runEtag) headers["If-None-Match"] = state.runEtag;
    try {
        const {response, data} = await apiFetch(`/test-runs/${state.selectedRunId}`, {headers});
        const indicator = document.getElementById("etag-indicator");
        if (response.status === 304) {
            indicator.textContent = `304 Not Modified — showing cached data (ETag ${state.runEtag}).`;
            return;
        }
        if (response.status === 404) {
            showToast("Run not found (it may have been deleted).", "error");
            closeDetail();
            return;
        }
        if (!response.ok) {
            showToast(`Failed to load run: HTTP ${response.status}`, "error");
            return;
        }
        state.runEtag = response.headers.get("ETag");
        indicator.textContent = `200 OK — fresh data. ETag=${state.runEtag}`;
        renderOverview(data);
    } catch (err) {
        showToast(err.message, "error");
    }
}

function renderOverview(run) {
    const el = document.getElementById("overview-content");
    const attackCategories = run.attack_categories || [];
    el.innerHTML = [
        ["Status", `<span class="badge ${statusBadgeClass(run.status)}">${escapeHtml(run.status || "unknown")}</span>`],
        ["Status error", escapeHtml(run.status_error) || "—"],
        ["Start", formatDateTime(run.timestamp && run.timestamp.start)],
        ["End", formatDateTime(run.timestamp && run.timestamp.end)],
        ["Test cases", String(attackCategories.length)],
        ["Total attacks", String(attackCategories.reduce((n, tc) => n + Object.keys(tc.attacks || {}).length, 0))],
    ].map(([label, value]) => `
    <div class="overview-item">
      <div class="label">${label}</div>
      <div class="value">${value}</div>
    </div>
  `).join("") + rawJsonBlock(run);
}

function startStatusPolling() {
    document.getElementById("poll-status-btn").classList.add("hidden");
    document.getElementById("stop-poll-btn").classList.remove("hidden");
    pollStatusOnce();
    state.statusPollTimer = setInterval(pollStatusOnce, 2000);
}

function stopStatusPolling() {
    if (state.statusPollTimer) {
        clearInterval(state.statusPollTimer);
        state.statusPollTimer = null;
    }
    document.getElementById("poll-status-btn").classList.remove("hidden");
    document.getElementById("stop-poll-btn").classList.add("hidden");
}

async function pollStatusOnce() {
    if (!state.selectedRunId) return;
    try {
        const {response, data} = await apiFetch(`/test-runs/${state.selectedRunId}/status`);
        const log = document.getElementById("status-poll-log");
        if (!response.ok) {
            stopStatusPolling();
            showToast(`Status poll failed: HTTP ${response.status}`, "error");
            return;
        }
        const line = document.createElement("div");
        line.textContent = `${new Date().toLocaleTimeString()} — status=${data.status}${data.status_error ? `, error=${data.status_error}` : ""}`;
        log.prepend(line);
        if (data.status === "completed" || data.status === "failed") {
            stopStatusPolling();
            showToast(`Run ${data.status}`, data.status === "completed" ? "success" : "error");
            loadOverview();
            loadTestCases();
            loadAnalyses();
        }
    } catch (err) {
        stopStatusPolling();
        showToast(err.message, "error");
    }
}

async function loadTestCases() {
    if (!state.selectedRunId) return;
    const size = parseInt(document.getElementById("tc-filter-size").value, 10) || 10;
    state.testCases.size = size;
    const params = new URLSearchParams({page: String(state.testCases.page), size: String(size)});
    renderTableLoading("#test-cases-table tbody", 7, "Loading test cases…");
    try {
        const {response, data} = await apiFetch(`/test-runs/${state.selectedRunId}/test-cases?${params.toString()}`);
        if (!response.ok) {
            showToast(`Failed to load test cases: HTTP ${response.status}`, "error");
            return;
        }
        renderTestCasesTable(data.content || []);
        renderPagination("test-cases-pagination", data.page.number, data.page.size, data.page.total_elements, data.page.total_pages, (p) => {
            state.testCases.page = p;
            loadTestCases();
        });
    } catch (err) {
        showToast(err.message, "error");
    }
}

function renderTestCasesTable(testCases) {
    const tbody = document.querySelector("#test-cases-table tbody");
    if (!testCases.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="muted">No test cases found.</td></tr>`;
        return;
    }
    tbody.innerHTML = testCases.map((tc) => `
    <tr>
      <td>${tc.id ?? "—"}</td>
      <td>${escapeHtml(tc.category)}</td>
      <td>${(tc.subcategories || []).map((s) => `<span class="chip">${escapeHtml(s)}</span>`).join("") || "—"}</td>
      <td>${escapeHtml((tc.model && tc.model.attack_and_vulnerability_generation) || "—")}</td>
      <td>${Object.keys(tc.attacks || {}).length}</td>
      <td>${tc.generation_error || tc.enhancement_error ? "⚠️" : ""}</td>
      <td><button class="small view-test-case-btn" data-tc-id="${tc.id}">View</button></td>
    </tr>
  `).join("");
    tbody.querySelectorAll(".view-test-case-btn").forEach((btn) => {
        btn.addEventListener("click", () => viewTestCase(btn.dataset.tcId));
    });
}

async function viewTestCase(testCaseId) {
    openModal(`<div class="overview-loading">${spinnerHtml("Loading test case…")}</div>`);
    try {
        const {response, data} = await apiFetch(`/test-runs/${state.selectedRunId}/test-cases/${testCaseId}`);
        if (response.status === 404) {
            showToast("Test case not found.", "error");
            closeModal();
            return;
        }
        if (!response.ok) {
            showToast(`Failed to load test case: HTTP ${response.status}`, "error");
            closeModal();
            return;
        }
        openModal(renderTestCaseDetail(data));
    } catch (err) {
        showToast(err.message, "error");
        closeModal();
    }
}

function renderTestCaseDetail(tc) {
    const attacks = Object.entries(tc.attacks || {});
    return `
    <h2>Test case #${tc.id ?? "?"} — ${escapeHtml(tc.category)}</h2>
    <p class="muted">Subcategories: ${(tc.subcategories || []).map((s) => `<span class="chip">${escapeHtml(s)}</span>`).join("") || "none"}</p>
    ${tc.generation_error ? `<p class="badge-danger badge">generation_error: ${escapeHtml(JSON.stringify(tc.generation_error))}</p>` : ""}
    ${tc.enhancement_error ? `<p class="badge-danger badge">enhancement_error: ${escapeHtml(JSON.stringify(tc.enhancement_error))}</p>` : ""}
    <h3>Attacks (${attacks.length})</h3>
    ${attacks.map(([id, attack]) => renderAttack(id, attack)).join("") || '<p class="muted">No attacks.</p>'}
    ${rawJsonBlock(tc)}
  `;
}

function renderAttack(id, attack) {
    const chatbotEntries = Object.entries(attack.llm_responses || {});
    const guardrailEntries = Object.entries(attack.protection || {});
    return `
    <details class="attack">
      <summary>
        <span class="badge ${attack.severity === "unsafe" ? "badge-danger" : "badge-neutral"}">${escapeHtml(attack.severity)}</span>
        ${escapeHtml(attack.category)}${attack.subcategory ? " / " + escapeHtml(attack.subcategory) : ""}
        ${(attack.techniques || []).map((t) => `<span class="chip">${escapeHtml(t)}</span>`).join("")}
      </summary>
      <div class="attack-body">
        <div class="prompt-pair">
          <div><strong>Baseline prompt</strong><p>${escapeHtml(attack.prompt && attack.prompt.baseline)}</p></div>
          <div><strong>Enhanced prompt</strong><p>${escapeHtml(attack.prompt && attack.prompt.enhanced)}</p></div>
        </div>
        ${chatbotEntries.map(([name, evalu]) => renderChatbotEval(name, evalu)).join("")}
        ${guardrailEntries.map(([name, perChatbot]) => renderGuardrail(name, perChatbot)).join("")}
        ${attack.error ? `<p class="badge-danger badge">error: ${escapeHtml(JSON.stringify(attack.error))}</p>` : ""}
      </div>
    </details>
  `;
}

function renderChatbotEval(name, evalu) {
    const resp = (evalu && evalu.chatbot_response) || {};
    return `
    <div class="chatbot-eval">
      <h4>${escapeHtml(name)}
        <span class="badge ${evalu.success ? "badge-success" : "badge-danger"}">${evalu.success ? "defended" : "attack succeeded"}</span>
        score=${evalu.score}
      </h4>
      <p class="muted">${escapeHtml(evalu.reason || "")}</p>
      <details><summary>Chatbot response</summary><p>${escapeHtml(resp.response || "")}</p></details>
    </div>
  `;
}

function renderGuardrail(name, perChatbot) {
    return Object.entries(perChatbot || {}).map(([chatbotName, dr]) => `
    <div class="guardrail-result">
      <h4>${escapeHtml(name)} — ${escapeHtml(chatbotName)}</h4>
      <div class="detection-pair">
        ${renderDetectionElement("Input", dr.input_detection)}
        ${renderDetectionElement("Output", dr.output_detection)}
      </div>
    </div>
  `).join("");
}

function renderDetectionElement(label, de) {
    if (!de) return "";
    const scanners = (de.scanner_details || []).map((s) => `
    <tr>
      <td>${escapeHtml(s.name)}</td>
      <td>${s.score}</td>
      <td>${s.is_valid === null || s.is_valid === undefined ? "—" : (s.is_valid ? "valid" : "invalid")}</td>
      <td>${escapeHtml(s.reason || "")}</td>
    </tr>
  `).join("");
    return `
    <div class="detection">
      <strong>${label}</strong>
      <span class="badge ${de.success ? "badge-success" : "badge-danger"}">${de.success ? "detected" : "missed"}</span>
      score=${de.score}
      ${scanners ? `<table class="mini-table"><thead><tr><th>Scanner</th><th>Score</th><th>Valid</th><th>Reason</th></tr></thead><tbody>${scanners}</tbody></table>` : ""}
    </div>
  `;
}

async function loadAnalyses() {
    if (!state.selectedRunId) return;
    renderTableLoading("#analyses-table tbody", 6, "Loading analyses…");
    try {
        const {response, data} = await apiFetch(`/test-runs/${state.selectedRunId}/analyses`);
        if (!response.ok) {
            showToast(`Failed to load analyses: HTTP ${response.status}`, "error");
            return;
        }
        renderAnalysesTable(data || []);
    } catch (err) {
        showToast(err.message, "error");
    }
}

function renderAnalysesTable(analyses) {
    const tbody = document.querySelector("#analyses-table tbody");
    if (!analyses.length) {
        tbody.innerHTML = `<tr><td colspan="6" class="muted">No analyses yet — analyses are computed automatically once the run completes.</td></tr>`;
        return;
    }
    tbody.innerHTML = analyses.map((a) => `
    <tr>
      <td>${a.id}</td>
      <td>consider_chatbot_success=${a.consider_chatbot_success}</td>
      <td>${a.exclude_scanners}</td>
      <td>${formatDateTime(a.created_at)}</td>
      <td>${a.version ?? "—"}</td>
      <td><button class="small view-analysis-btn" data-analysis-id="${a.id}">View</button></td>
    </tr>
  `).join("");
    tbody.querySelectorAll(".view-analysis-btn").forEach((btn) => {
        btn.addEventListener("click", () => viewAnalysis(btn.dataset.analysisId));
    });
}

async function viewAnalysis(analysisId, useEtag = false) {
    const headers = {};
    const cachedEtag = state.analysisEtags.get(analysisId);
    if (useEtag && cachedEtag) headers["If-None-Match"] = cachedEtag;

    let restoreButton = () => {};
    if (!useEtag) {
        openModal(`<div class="overview-loading">${spinnerHtml("Loading analysis…")}</div>`);
    } else {
        restoreButton = beginButtonLoading(document.getElementById("modal-refresh-analysis-btn"), "Checking…");
    }

    try {
        const {response, data} = await apiFetch(`/test-runs/${state.selectedRunId}/analyses/${analysisId}`, {headers});
        if (response.status === 304) {
            showToast("304 Not Modified (analysis versions never change once created).", "success");
            return;
        }
        if (response.status === 404) {
            showToast("Analysis not found.", "error");
            if (!useEtag) closeModal();
            return;
        }
        if (!response.ok) {
            showToast(`Failed to load analysis: HTTP ${response.status}`, "error");
            if (!useEtag) closeModal();
            return;
        }
        state.analysisEtags.set(analysisId, response.headers.get("ETag"));
        openModal(renderAnalysisDetail(data, response.headers.get("ETag")));
        const refreshBtn = document.getElementById("modal-refresh-analysis-btn");
        if (refreshBtn) refreshBtn.addEventListener("click", () => viewAnalysis(analysisId, true));
    } catch (err) {
        showToast(err.message, "error");
        if (!useEtag) closeModal();
    } finally {
        restoreButton();
    }
}

function renderAnalysisDetail(analysis, etag) {
    return `
    <h2>Analysis #${analysis.id}</h2>
    <p class="muted">
      exclude_scanners=${analysis.exclude_scanners}, consider_chatbot_success=${analysis.consider_chatbot_success},
      created=${formatDateTime(analysis.created_at)}, ETag=${escapeHtml(etag)}
    </p>
    <button class="small" id="modal-refresh-analysis-btn">Refresh with If-None-Match (expect 304)</button>
    <h3>Summary rows</h3>
    ${renderSummaryTable(analysis.summary_rows || [])}
    <h3>Summary errors</h3>
    ${renderSummaryErrors(analysis.summary_errors || [])}
    ${rawJsonBlock(analysis)}
  `;
}

function renderSummaryTable(rows) {
    if (!rows.length) return '<p class="muted">No summary rows.</p>';
    const grouped = new Map();
    for (const row of rows) {
        if (!grouped.has(row.node)) grouped.set(row.node, []);
        grouped.get(row.node).push(row);
    }
    return Array.from(grouped.entries()).map(([node, group]) => `
    <h4>${escapeHtml(node)}</h4>
    <table class="mini-table">
      <thead><tr><th>Scope</th><th>Category</th><th>Technique</th><th>Count</th><th>TP</th><th>FP</th><th>TN</th><th>FN</th></tr></thead>
      <tbody>
        ${group.map((r) => `
          <tr>
            <td>${escapeHtml(r.scope)}</td>
            <td>${escapeHtml(r.attack_category)}</td>
            <td>${escapeHtml(r.technique)}</td>
            <td>${r.count}</td><td>${r.tp}</td><td>${r.fp}</td><td>${r.tn}</td><td>${r.fn}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `).join("");
}

function renderSummaryErrors(errors) {
    if (!errors.length) return '<p class="muted">No errors recorded.</p>';
    return `
    <table class="mini-table">
      <thead><tr><th>Node</th><th>Category</th><th>Count</th></tr></thead>
      <tbody>
        ${errors.map((e) => `<tr><td>${escapeHtml(e.node)}</td><td>${escapeHtml(e.attack_category)}</td><td>${e.count}</td></tr>`).join("")}
      </tbody>
    </table>
  `;
}

async function exportAnalyses() {
    if (!state.selectedRunId) return;
    const variant = document.getElementById("export-variant").value;
    const excludeScanners = document.getElementById("export-exclude-scanners").checked;
    const params = new URLSearchParams({exclude_scanners: String(excludeScanners)});
    if (variant) params.set("consider_chatbot_success", variant);
    const done = beginButtonLoading(document.getElementById("export-btn"), "Preparing…");
    try {
        const {
            response,
            data
        } = await apiFetch(`/test-runs/${state.selectedRunId}/analyses/export?${params.toString()}`);
        if (response.status === 404) {
            showToast("No analyses match this filter.", "error");
            return;
        }
        if (!response.ok || !data) {
            showToast(`Export failed: HTTP ${response.status}`, "error");
            return;
        }
        const disposition = response.headers.get("Content-Disposition") || "";
        const match = disposition.match(/filename="?([^"]+)"?/);
        const filename = match ? match[1] : `analyses_${state.selectedRunId}.zip`;
        const url = URL.createObjectURL(data);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        showToast(`Downloaded ${filename}`, "success");
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        done();
    }
}

async function deleteRun() {
    if (!state.selectedRunId) return;
    if (!confirm(`Delete run ${state.selectedRunId} and everything attached to it? This cannot be undone.`)) return;
    const done = beginButtonLoading(document.getElementById("delete-run-btn"), "Deleting…");
    try {
        const {response} = await apiFetch(`/test-runs/${state.selectedRunId}`, {method: "DELETE"});
        if (response.status === 204) {
            showToast("Run deleted", "success");
            closeDetail();
            loadRuns();
        } else if (response.status === 404) {
            showToast("Run was already gone.", "error");
            closeDetail();
            loadRuns();
        } else {
            showToast(`Delete failed: HTTP ${response.status}`, "error");
        }
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        done();
    }
}

function wireEvents() {
    document.getElementById("api-base").value = state.apiBase;
    document.getElementById("save-config-btn").addEventListener("click", () => {
        const value = document.getElementById("api-base").value.trim() || DEFAULT_API_BASE;
        state.apiBase = value;
        localStorage.setItem("apiBase", value);
        showToast("API base URL saved", "success");
        checkHealth();
        loadRuns();
    });
    document.getElementById("refresh-health-btn").addEventListener("click", checkHealth);

    document.getElementById("start-run-btn").addEventListener("click", startRun);
    document.getElementById("refresh-runs-btn").addEventListener("click", async () => {
        const done = beginButtonLoading(document.getElementById("refresh-runs-btn"), "Refreshing…");
        state.runs.page = 0;
        await loadRuns();
        done();
    });

    document.getElementById("close-detail-btn").addEventListener("click", closeDetail);
    document.querySelectorAll(".tab-btn").forEach((btn) => {
        btn.addEventListener("click", () => switchTab(btn.dataset.tab));
    });

    document.getElementById("refresh-overview-btn").addEventListener("click", async () => {
        const done = beginButtonLoading(document.getElementById("refresh-overview-btn"), "Refreshing…");
        await loadOverview(true);
        done();
    });
    document.getElementById("poll-status-btn").addEventListener("click", startStatusPolling);
    document.getElementById("stop-poll-btn").addEventListener("click", stopStatusPolling);
    document.getElementById("delete-run-btn").addEventListener("click", deleteRun);

    document.getElementById("refresh-test-cases-btn").addEventListener("click", async () => {
        const done = beginButtonLoading(document.getElementById("refresh-test-cases-btn"), "Refreshing…");
        state.testCases.page = 0;
        await loadTestCases();
        done();
    });
    document.getElementById("refresh-analyses-btn").addEventListener("click", async () => {
        const done = beginButtonLoading(document.getElementById("refresh-analyses-btn"), "Refreshing…");
        await loadAnalyses();
        done();
    });
    document.getElementById("export-btn").addEventListener("click", exportAnalyses);

    document.getElementById("modal-close-btn").addEventListener("click", closeModal);
    document.getElementById("modal-backdrop").addEventListener("click", (evt) => {
        if (evt.target.id === "modal-backdrop") closeModal();
    });
    document.addEventListener("keydown", (evt) => {
        if (evt.key === "Escape") closeModal();
    });
}

wireEvents();
checkHealth();
loadRuns();
