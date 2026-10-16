/**
 * BlindSpot Web Demonstration Controller
 * Manages test submission, real-time SSE progress streaming, live viewport, and results dashboard.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements - Views
  const viewSetup = document.getElementById("viewSetup");
  const viewLive = document.getElementById("viewLive");
  const viewResults = document.getElementById("viewResults");

  // DOM Elements - Form & Controls
  const testForm = document.getElementById("testForm");
  const inputUrl = document.getElementById("inputUrl");
  const inputContext = document.getElementById("inputContext");
  const inputPersonas = document.getElementById("inputPersonas");
  const personasCountDisplay = document.getElementById("personasCountDisplay");
  const selectBrowser = document.getElementById("selectBrowser");
  const checkHeaded = document.getElementById("checkHeaded");
  const btnSubmitTest = document.getElementById("btnSubmitTest");
  const formErrorAlert = document.getElementById("formErrorAlert");

  // DOM Elements - Nav
  const btnNewTestNav = document.getElementById("btnNewTestNav");
  const btnHistoryNav = document.getElementById("btnHistoryNav");
  const historyModal = document.getElementById("historyModal");
  const btnCloseHistoryModal = document.getElementById("btnCloseHistoryModal");
  const historyListContainer = document.getElementById("historyListContainer");

  // DOM Elements - Live View
  const liveTargetUrl = document.getElementById("liveTargetUrl");
  const liveRunId = document.getElementById("liveRunId");
  const liveStatusBadge = document.getElementById("liveStatusBadge");
  const liveTimer = document.getElementById("liveTimer");
  const liveMessage = document.getElementById("liveMessage");
  const btnCancelRun = document.getElementById("btnCancelRun");
  const livePersonaName = document.getElementById("livePersonaName");
  const liveTaskObjective = document.getElementById("liveTaskObjective");
  const liveActionBadge = document.getElementById("liveActionBadge");
  const liveScreenshotImg = document.getElementById("liveScreenshotImg");
  const viewportPlaceholder = document.getElementById("viewportPlaceholder");
  const eventStreamLog = document.getElementById("eventStreamLog");
  const eventCountBadge = document.getElementById("eventCountBadge");

  // Stepper Elements
  const stepInspection = document.getElementById("stepInspection");
  const stepPersonas = document.getElementById("stepPersonas");
  const stepExecution = document.getElementById("stepExecution");
  const stepReporting = document.getElementById("stepReporting");

  // DOM Elements - Results View
  const resultTargetUrl = document.getElementById("resultTargetUrl");
  const resultWebsiteSummary = document.getElementById("resultWebsiteSummary");
  const btnViewHtmlReport = document.getElementById("btnViewHtmlReport");
  const btnDownloadJsonReport = document.getElementById("btnDownloadJsonReport");
  const metricTasksPassed = document.getElementById("metricTasksPassed");
  const metricTasksSub = document.getElementById("metricTasksSub");
  const metricVerifiedIssues = document.getElementById("metricVerifiedIssues");
  const metricUsabilityObservations = document.getElementById("metricUsabilityObservations");
  const metricPotentialImprovements = document.getElementById("metricPotentialImprovements");
  const resultsPersonasContainer = document.getElementById("resultsPersonasContainer");
  const resultsFindingsList = document.getElementById("resultsFindingsList");

  // Filter Tabs
  const countTabAll = document.getElementById("countTabAll");
  const countTabVerified = document.getElementById("countTabVerified");
  const countTabUsability = document.getElementById("countTabUsability");
  const countTabImprovement = document.getElementById("countTabImprovement");
  const tabButtons = document.querySelectorAll(".tab-btn");

  // State
  let currentRunId = null;
  let eventSource = null;
  let timerInterval = null;
  let timerStart = null;
  let eventCount = 0;
  let currentReportData = null;
  let currentFilterCategory = "ALL";

  // 1. Preset Buttons Handler
  document.querySelectorAll(".btn-preset").forEach((btn) => {
    btn.addEventListener("click", () => {
      inputUrl.value = btn.getAttribute("data-url") || "";
      inputContext.value = btn.getAttribute("data-ctx") || "";
      formErrorAlert.style.display = "none";
    });
  });

  // 2. Persona Slider Listener
  inputPersonas.addEventListener("input", (e) => {
    personasCountDisplay.textContent = e.target.value;
  });

  // 3. Navigation Actions
  btnNewTestNav.addEventListener("click", () => {
    cleanupStreaming();
    showView("setup");
  });

  btnHistoryNav.addEventListener("click", () => {
    openHistoryModal();
  });

  btnCloseHistoryModal.addEventListener("click", () => {
    historyModal.style.display = "none";
  });

  // 4. Test Submission Form Handler
  testForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    formErrorAlert.style.display = "none";

    const targetUrl = inputUrl.value.trim();
    const context = inputContext.value.trim();
    const personasCount = parseInt(inputPersonas.value, 10);
    const browser = selectBrowser.value;
    const headed = checkHeaded.checked;

    if (!targetUrl.startsWith("http://") && !targetUrl.startsWith("https://")) {
      showFormError("URL must start with http:// or https://");
      return;
    }

    btnSubmitTest.disabled = true;
    btnSubmitTest.innerHTML = `<div class="spinner"></div> Starting Test...`;

    try {
      const resp = await fetch("/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: targetUrl,
          context: context,
          personas: personasCount,
          browser: browser,
          headed: headed,
        }),
      });

      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || "Failed to start test run.");
      }

      currentRunId = data.run_id;
      startLiveView(currentRunId, targetUrl);
    } catch (err) {
      showFormError(err.message);
    } finally {
      btnSubmitTest.disabled = false;
      btnSubmitTest.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        Start Automated UX Test
      `;
    }
  });

  function showFormError(msg) {
    formErrorAlert.textContent = msg;
    formErrorAlert.style.display = "block";
  }

  // 5. Live View Logic
  function startLiveView(runId, url) {
    showView("live");
    liveRunId.textContent = runId;
    liveTargetUrl.textContent = url;
    liveStatusBadge.className = "status-badge badge-running";
    liveStatusBadge.textContent = "RUNNING";
    liveMessage.textContent = "Initializing test environment...";
    livePersonaName.textContent = "Synthesizing...";
    liveTaskObjective.textContent = "Waiting for execution...";
    liveActionBadge.textContent = "[INITIALIZING]";
    liveScreenshotImg.style.display = "none";
    viewportPlaceholder.style.display = "flex";
    eventStreamLog.innerHTML = "";
    eventCount = 0;
    eventCountBadge.textContent = "0 events";

    resetStepper();
    stepInspection.classList.add("step-active");

    // Start timer
    timerStart = Date.now();
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      const elapsedSec = Math.floor((Date.now() - timerStart) / 1000);
      const mins = String(Math.floor(elapsedSec / 60)).padStart(2, "0");
      const secs = String(elapsedSec % 60).padStart(2, "0");
      liveTimer.textContent = `${mins}:${secs}`;
    }, 1000);

    // Connect Server-Sent Events (SSE)
    connectEventSource(runId);
  }

  function connectEventSource(runId) {
    cleanupStreaming();

    eventSource = new EventSource(`/api/runs/${runId}/events`);

    eventSource.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data);
        handleStreamEvent(evt);
      } catch (err) {
        console.error("Malformed SSE event:", err);
      }
    };

    eventSource.onerror = (err) => {
      console.warn("EventSource disconnected or completed.");
      // Fallback check status after a moment
      checkRunStatusFallback(runId);
    };
  }

  function handleStreamEvent(evt) {
    eventCount++;
    eventCountBadge.textContent = `${eventCount} events`;
    appendLogEntry(evt);

    const type = evt.type || "";
    if (type === "stage_start") {
      updateStageActive(evt.stage);
      liveMessage.textContent = evt.message || `Starting ${evt.stage}...`;
    } else if (type === "stage_finish") {
      if (evt.stage === "inspection" && evt.screenshot_path) {
        updateViewportScreenshot(evt.screenshot_path);
      }
    } else if (type === "action_step") {
      livePersonaName.textContent = evt.persona_name || "Active Persona";
      liveTaskObjective.textContent = evt.task_objective || "";
      liveActionBadge.textContent = `[${(evt.action || "STEP").toUpperCase()}]`;
      if (evt.screenshot_path) {
        updateViewportScreenshot(evt.screenshot_path);
      }
    } else if (type === "task_start") {
      livePersonaName.textContent = evt.persona_name || "Active Persona";
      liveTaskObjective.textContent = evt.task_objective || "";
      liveActionBadge.textContent = "[TASK_START]";
    } else if (type === "pipeline_finish") {
      liveStatusBadge.className = "status-badge badge-completed";
      liveStatusBadge.textContent = "COMPLETED";
      liveMessage.textContent = "Analysis complete! Loading dashboard...";
      cleanupStreaming();
      setTimeout(() => loadAndShowResults(currentRunId), 1200);
    } else if (type === "pipeline_cancelled") {
      liveStatusBadge.className = "status-badge badge-cancelled";
      liveStatusBadge.textContent = "CANCELLED";
      liveMessage.textContent = "Test run was cancelled by user.";
      cleanupStreaming();
    } else if (type === "pipeline_error") {
      liveStatusBadge.className = "status-badge badge-failed";
      liveStatusBadge.textContent = "FAILED";
      liveMessage.textContent = `Error: ${evt.error || "Unknown error"}`;
      cleanupStreaming();
    }
  }

  function appendLogEntry(evt) {
    const entry = document.createElement("div");
    entry.className = "log-entry";

    const timeStr = new Date().toLocaleTimeString();
    const type = evt.type || "event";

    if (type === "stage_start" || type === "stage_finish") {
      entry.classList.add("log-entry-stage");
      entry.textContent = `[${timeStr}] ${type.toUpperCase()}: ${evt.stage || ""} - ${evt.message || ""}`;
    } else if (type === "action_step") {
      entry.classList.add("log-entry-step");
      entry.textContent = `[${timeStr}] ACTION [${evt.action}]: ${evt.target || ""} -> ${evt.reasoning || ""}`;
    } else if (type === "pipeline_error") {
      entry.classList.add("log-entry-error");
      entry.textContent = `[${timeStr}] ERROR: ${evt.error || ""}`;
    } else {
      entry.textContent = `[${timeStr}] ${type.toUpperCase()}: ${JSON.stringify(evt)}`;
    }

    eventStreamLog.appendChild(entry);
    eventStreamLog.scrollTop = eventStreamLog.scrollHeight;
  }

  function updateViewportScreenshot(pathStr) {
    if (!pathStr) return;
    const filename = pathStr.split(/[\\/]/).pop();
    const url = `/api/runs/${currentRunId}/reports/${filename}?t=${Date.now()}`;
    liveScreenshotImg.src = url;
    liveScreenshotImg.style.display = "block";
    viewportPlaceholder.style.display = "none";
  }

  function updateStageActive(stageName) {
    resetStepper();
    if (stageName === "inspection") {
      stepInspection.classList.add("step-active");
    } else if (stageName === "personas") {
      stepInspection.classList.add("step-active");
      stepPersonas.classList.add("step-active");
    } else if (stageName === "execution") {
      stepInspection.classList.add("step-active");
      stepPersonas.classList.add("step-active");
      stepExecution.classList.add("step-active");
    } else if (stageName === "reporting") {
      stepInspection.classList.add("step-active");
      stepPersonas.classList.add("step-active");
      stepExecution.classList.add("step-active");
      stepReporting.classList.add("step-active");
    }
  }

  function resetStepper() {
    stepInspection.className = "step";
    stepPersonas.className = "step";
    stepExecution.className = "step";
    stepReporting.className = "step";
  }

  async function checkRunStatusFallback(runId) {
    try {
      const resp = await fetch(`/api/runs/${runId}`);
      if (!resp.ok) return;
      const statusData = await resp.json();
      if (statusData.status === "completed") {
        cleanupStreaming();
        loadAndShowResults(runId);
      } else if (statusData.status === "failed" || statusData.status === "cancelled") {
        cleanupStreaming();
        liveStatusBadge.className = `status-badge badge-${statusData.status}`;
        liveStatusBadge.textContent = statusData.status.toUpperCase();
        liveMessage.textContent = statusData.progress_message || statusData.error_message || "";
      }
    } catch (err) {
      console.warn("Status fallback error:", err);
    }
  }

  // 6. Cancel Run Action
  btnCancelRun.addEventListener("click", async () => {
    if (!currentRunId) return;
    btnCancelRun.disabled = true;
    try {
      await fetch(`/api/runs/${currentRunId}/cancel`, { method: "POST" });
      liveMessage.textContent = "Cancelling test run...";
    } catch (err) {
      console.error("Cancel failed:", err);
    }
  });

  // 7. Results Dashboard Logic
  async function loadAndShowResults(runId) {
    try {
      const resp = await fetch(`/api/runs/${runId}/results`);
      if (!resp.ok) throw new Error("Report results not ready.");
      const report = await resp.json();
      currentReportData = report;
      renderResultsDashboard(report, runId);
      showView("results");
    } catch (err) {
      console.error("Failed to load results:", err);
    }
  }

  function renderResultsDashboard(report, runId) {
    resultTargetUrl.textContent = report.target_url || "Target Website";
    resultWebsiteSummary.textContent = report.website_summary || "";

    btnViewHtmlReport.href = `/api/runs/${runId}/reports/report.html`;
    btnDownloadJsonReport.href = `/api/runs/${runId}/reports/report.json`;

    const metrics = report.task_metrics || {};
    metricTasksPassed.textContent = `${metrics.passed_tasks || 0} / ${metrics.total_tasks || 0}`;
    metricTasksSub.textContent = `${metrics.failed_tasks || 0} failures, ${metrics.inconclusive_tasks || 0} inconclusive`;

    metricVerifiedIssues.textContent = report.verified_issues_count || 0;
    metricUsabilityObservations.textContent = report.usability_observations_count || 0;
    metricPotentialImprovements.textContent = report.potential_improvements_count || 0;

    // Filter tab counts
    const findings = report.findings || [];
    countTabAll.textContent = findings.length;
    countTabVerified.textContent = findings.filter(f => f.category === "OBJECTIVE_DEFECT").length;
    countTabUsability.textContent = findings.filter(f => f.category === "USABILITY_OBSERVATION").length;
    countTabImprovement.textContent = findings.filter(f => f.category === "POTENTIAL_IMPROVEMENT").length;

    // Render Personas
    resultsPersonasContainer.innerHTML = "";
    const personasList = report.personas_summary || report.persona_summaries || [];
    personasList.forEach((p) => {
      const box = document.createElement("div");
      box.className = "persona-box";

      const header = document.createElement("div");
      header.className = "persona-box-header";
      const name = p.name || p.persona_name || "Simulated User";
      const role = p.experience || p.role || p.style_or_needs || "";
      header.innerHTML = `
        <span class="persona-title">${escapeHtml(name)}</span>
        <span class="persona-role">${escapeHtml(role)}</span>
      `;
      box.appendChild(header);

      const goals = document.createElement("div");
      goals.className = "persona-goals";
      const goalsText = Array.isArray(p.goals) ? p.goals.join(", ") : (p.style_or_needs || "Autonomous exploratory journey");
      goals.textContent = `Focus: ${goalsText}`;
      box.appendChild(goals);

      const tasksList = document.createElement("div");
      tasksList.className = "persona-tasks-list";

      const personaTasks = (report.task_summaries || []).filter(t => t.persona_id === (p.id || p.persona_id));
      if (personaTasks.length > 0) {
        personaTasks.forEach((t) => {
          const item = document.createElement("div");
          item.className = "task-item";
          const isPass = t.status === "SUCCESS";
          item.innerHTML = `
            <span class="text-truncate">${escapeHtml(t.task_objective || t.objective || "")}</span>
            <span class="status-badge ${isPass ? 'badge-completed' : 'badge-failed'}">${escapeHtml(t.status || "")}</span>
          `;
          tasksList.appendChild(item);
        });
      } else {
        const item = document.createElement("div");
        item.className = "task-item dim";
        item.textContent = `${p.tasks_count || 0} tasks assigned`;
        tasksList.appendChild(item);
      }

      box.appendChild(tasksList);
      resultsPersonasContainer.appendChild(box);
    });

    renderFindingsList();
  }

  // Filter Tabs Event Listeners
  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentFilterCategory = btn.getAttribute("data-category") || "ALL";
      renderFindingsList();
    });
  });

  function renderFindingsList() {
    resultsFindingsList.innerHTML = "";
    if (!currentReportData || !currentReportData.findings) return;

    const filtered = currentReportData.findings.filter((f) => {
      if (currentFilterCategory === "ALL") return true;
      return f.category === currentFilterCategory;
    });

    if (filtered.length === 0) {
      resultsFindingsList.innerHTML = `<div class="dim" style="padding: 1.5rem; text-align: center;">No findings in this category.</div>`;
      return;
    }

    filtered.forEach((f) => {
      const card = document.createElement("div");
      card.className = "finding-card";

      const top = document.createElement("div");
      top.className = "finding-top";

      const badges = document.createElement("div");
      badges.className = "finding-badges";

      const sev = (f.severity || "INFORMATIONAL").toLowerCase();
      const catLabel = formatCategoryLabel(f.category);

      badges.innerHTML = `
        <span class="code-badge">${escapeHtml(f.id)}</span>
        <span class="sev-badge sev-${sev}">${escapeHtml(f.severity)}</span>
        <span class="cat-badge">${escapeHtml(catLabel)}</span>
      `;
      top.appendChild(badges);

      const conf = document.createElement("span");
      conf.className = "dim";
      conf.style.fontSize = "0.75rem";
      conf.textContent = `Confidence: ${Math.round((f.confidence || 0) * 100)}%`;
      top.appendChild(conf);

      card.appendChild(top);

      const title = document.createElement("h4");
      title.className = "finding-title";
      title.textContent = f.title;
      card.appendChild(title);

      const desc = document.createElement("p");
      desc.className = "finding-desc";
      desc.textContent = f.description;
      card.appendChild(desc);

      if (f.supporting_evidence && f.supporting_evidence.length > 0) {
        const ev = document.createElement("div");
        ev.className = "finding-evidence";
        ev.textContent = `Evidence: ${f.supporting_evidence.join(" | ")}`;
        card.appendChild(ev);
      }

      if (f.reproduction_steps && f.reproduction_steps.length > 0) {
        const repro = document.createElement("div");
        repro.className = "finding-repro";
        repro.innerHTML = `<strong>Reproduction Steps:</strong><ol>${f.reproduction_steps.map(s => `<li>${escapeHtml(s)}</li>`).join("")}</ol>`;
        card.appendChild(repro);
      }

      if (f.suggested_improvement) {
        const fix = document.createElement("div");
        fix.className = "finding-fix";
        fix.innerHTML = `<strong>Suggested Fix:</strong> ${escapeHtml(f.suggested_improvement)}`;
        if (f.expected_benefit) {
          fix.innerHTML += ` <div class="dim" style="margin-top: 0.25rem;"><em>Benefit:</em> ${escapeHtml(f.expected_benefit)}</div>`;
        }
        card.appendChild(fix);
      }

      resultsFindingsList.appendChild(card);
    });
  }

  function formatCategoryLabel(cat) {
    if (cat === "OBJECTIVE_DEFECT") return "Verified Defect";
    if (cat === "USABILITY_OBSERVATION") return "Usability Observation";
    if (cat === "POTENTIAL_IMPROVEMENT") return "Potential Improvement";
    return cat || "Finding";
  }

  // 8. History Modal Logic
  async function openHistoryModal() {
    historyModal.style.display = "flex";
    historyListContainer.innerHTML = `<div class="spinner" style="margin: 2rem auto;"></div>`;

    try {
      const resp = await fetch("/api/runs");
      if (!resp.ok) throw new Error("Failed to load history.");
      const runs = await resp.json();

      historyListContainer.innerHTML = "";
      if (runs.length === 0) {
        historyListContainer.innerHTML = `<div class="dim" style="padding: 2rem; text-align: center;">No test runs found.</div>`;
        return;
      }

      runs.forEach((r) => {
        const item = document.createElement("div");
        item.className = "history-item";

        const left = document.createElement("div");
        left.innerHTML = `
          <div class="history-url">${escapeHtml(r.target_url)}</div>
          <div class="history-meta">${escapeHtml(r.run_id)} • ${new Date(r.created_at).toLocaleString()} • ${r.findings_count} findings</div>
        `;

        const right = document.createElement("div");
        const btnView = document.createElement("button");
        btnView.className = "btn btn-secondary btn-sm";
        btnView.textContent = "View Results";
        btnView.addEventListener("click", () => {
          historyModal.style.display = "none";
          currentRunId = r.run_id;
          loadAndShowResults(r.run_id);
        });
        right.appendChild(btnView);

        item.appendChild(left);
        item.appendChild(right);
        historyListContainer.appendChild(item);
      });
    } catch (err) {
      historyListContainer.innerHTML = `<div class="alert alert-error">${escapeHtml(err.message)}</div>`;
    }
  }

  // 9. View Switcher & Helper Functions
  function showView(viewName) {
    viewSetup.style.display = viewName === "setup" ? "block" : "none";
    viewLive.style.display = viewName === "live" ? "block" : "none";
    viewResults.style.display = viewName === "results" ? "block" : "none";

    btnNewTestNav.style.display = viewName === "setup" ? "none" : "inline-flex";
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function cleanupStreaming() {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
    clearInterval(timerInterval);
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
