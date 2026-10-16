/**
 * BlindSpot Web Demonstration Controller
 * Manages full-screen target website display, compact context navbar,
 * click-to-open UX details overlay, real-time SSE progress streaming,
 * and comprehensive usability report inspection.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements - Views
  const viewSetup = document.getElementById("viewSetup");
  const viewFullscreenWebsite = document.getElementById("viewFullscreenWebsite");

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

  // DOM Elements - Navbar & Context
  const brandHome = document.getElementById("brandHome");
  const navTestContext = document.getElementById("navTestContext");
  const navTargetUrl = document.getElementById("navTargetUrl");
  const navTargetUrlText = document.getElementById("navTargetUrlText");
  const navStatusBadge = document.getElementById("navStatusBadge");
  const navTimer = document.getElementById("navTimer");
  const navPersonaName = document.getElementById("navPersonaName");
  const navTaskObjective = document.getElementById("navTaskObjective");
  const btnOpenUxOverlay = document.getElementById("btnOpenUxOverlay");
  const navFindingsBadge = document.getElementById("navFindingsBadge");
  const navViewToggleGroup = document.getElementById("navViewToggleGroup");
  const btnViewWebsite = document.getElementById("btnViewWebsite");
  const btnViewAutomation = document.getElementById("btnViewAutomation");
  const btnCancelRunNav = document.getElementById("btnCancelRunNav");
  const btnNewTestNav = document.getElementById("btnNewTestNav");
  const btnHistoryNav = document.getElementById("btnHistoryNav");

  // DOM Elements - Fullscreen Website Viewport
  const targetWebsiteIframe = document.getElementById("targetWebsiteIframe");
  const frameSecurityBanner = document.getElementById("frameSecurityBanner");
  const btnExternalSite = document.getElementById("btnExternalSite");
  const automationFeedLayer = document.getElementById("automationFeedLayer");
  const fullscreenScreenshotImg = document.getElementById("fullscreenScreenshotImg");
  const automationPlaceholder = document.getElementById("automationPlaceholder");
  const feedPersonaText = document.getElementById("feedPersonaText");
  const feedActionText = document.getElementById("feedActionText");
  const btnReturnToWebsite = document.getElementById("btnReturnToWebsite");

  // DOM Elements - UX Details Overlay Modal
  const uxDetailsOverlay = document.getElementById("uxDetailsOverlay");
  const uxOverlayPanel = document.getElementById("uxOverlayPanel");
  const overlayTitle = document.getElementById("overlayTitle");
  const overlayStatusBadge = document.getElementById("overlayStatusBadge");
  const overlayTargetUrl = document.getElementById("overlayTargetUrl");
  const overlayRunId = document.getElementById("overlayRunId");
  const overlayTimer = document.getElementById("overlayTimer");
  const overlayMessage = document.getElementById("overlayMessage");
  const overlayBtnHtmlReport = document.getElementById("overlayBtnHtmlReport");
  const btnCloseUxOverlay = document.getElementById("btnCloseUxOverlay");

  // Overlay Tab Buttons & Panels
  const tabBtnLive = document.getElementById("tabBtnLive");
  const tabBtnPersonas = document.getElementById("tabBtnPersonas");
  const tabBtnFindings = document.getElementById("tabBtnFindings");
  const tabBtnReport = document.getElementById("tabBtnReport");
  const tabCountPersonas = document.getElementById("tabCountPersonas");
  const tabCountFindings = document.getElementById("tabCountFindings");

  const tabPanelLive = document.getElementById("tabPanelLive");
  const tabPanelPersonas = document.getElementById("tabPanelPersonas");
  const tabPanelFindings = document.getElementById("tabPanelFindings");
  const tabPanelReport = document.getElementById("tabPanelReport");

  // Stepper Elements
  const stepInspection = document.getElementById("stepInspection");
  const stepPersonas = document.getElementById("stepPersonas");
  const stepExecution = document.getElementById("stepExecution");
  const stepReporting = document.getElementById("stepReporting");

  // Overlay Tab 1 - Live Elements
  const livePersonaName = document.getElementById("livePersonaName");
  const liveTaskObjective = document.getElementById("liveTaskObjective");
  const liveActionBadge = document.getElementById("liveActionBadge");
  const liveScreenshotImg = document.getElementById("liveScreenshotImg");
  const viewportPlaceholder = document.getElementById("viewportPlaceholder");
  const eventStreamLog = document.getElementById("eventStreamLog");
  const eventCountBadge = document.getElementById("eventCountBadge");

  // Overlay Tab 2 & 3 & 4 - Results Elements
  const resultsPersonasContainer = document.getElementById("resultsPersonasContainer");
  const resultsFindingsList = document.getElementById("resultsFindingsList");
  const metricTasksPassed = document.getElementById("metricTasksPassed");
  const metricTasksSub = document.getElementById("metricTasksSub");
  const metricVerifiedIssues = document.getElementById("metricVerifiedIssues");
  const metricUsabilityObservations = document.getElementById("metricUsabilityObservations");
  const metricPotentialImprovements = document.getElementById("metricPotentialImprovements");
  const resultWebsiteSummary = document.getElementById("resultWebsiteSummary");
  const btnViewHtmlReport = document.getElementById("btnViewHtmlReport");
  const btnDownloadJsonReport = document.getElementById("btnDownloadJsonReport");

  // Filter Tabs
  const countTabAll = document.getElementById("countTabAll");
  const countTabVerified = document.getElementById("countTabVerified");
  const countTabUsability = document.getElementById("countTabUsability");
  const countTabImprovement = document.getElementById("countTabImprovement");
  const tabButtons = document.querySelectorAll(".tab-btn");

  // Past Runs Modal
  const historyModal = document.getElementById("historyModal");
  const btnCloseHistoryModal = document.getElementById("btnCloseHistoryModal");
  const historyListContainer = document.getElementById("historyListContainer");

  // Application State
  let currentRunId = null;
  let currentTargetUrl = "";
  let eventSource = null;
  let timerInterval = null;
  let timerStart = null;
  let eventCount = 0;
  let currentReportData = null;
  let currentFilterCategory = "ALL";
  let isOverlayOpen = false;
  let activeTabName = "tabPanelLive";
  let activeFullscreenView = "website"; // "website" | "automation"

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
  brandHome.addEventListener("click", () => {
    if (currentRunId && !confirm("Return to setup screen? Current test session view will be reset.")) {
      return;
    }
    resetToSetup();
  });

  btnNewTestNav.addEventListener("click", () => {
    resetToSetup();
  });

  btnHistoryNav.addEventListener("click", () => {
    openHistoryModal();
  });

  btnCloseHistoryModal.addEventListener("click", () => {
    historyModal.style.display = "none";
  });

  // 4. Details Overlay Open / Close Listeners
  btnOpenUxOverlay.addEventListener("click", () => {
    toggleUxOverlay();
  });

  btnCloseUxOverlay.addEventListener("click", () => {
    closeUxOverlay();
  });

  // Clicking on translucent backdrop (outside panel) closes overlay
  uxDetailsOverlay.addEventListener("click", (e) => {
    if (e.target === uxDetailsOverlay) {
      closeUxOverlay();
    }
  });

  // Escape key closes overlay safely
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" || e.key === "Esc") {
      if (isOverlayOpen) {
        closeUxOverlay();
      } else if (historyModal.style.display === "flex") {
        historyModal.style.display = "none";
      }
    }
  });

  function openUxOverlay(targetTab) {
    isOverlayOpen = true;
    uxDetailsOverlay.style.display = "flex";
    document.body.classList.add("overlay-open");

    // Accessibility focus management
    btnCloseUxOverlay.focus();

    if (targetTab) {
      switchOverlayTab(targetTab);
    }
  }

  function closeUxOverlay() {
    isOverlayOpen = false;
    uxDetailsOverlay.style.display = "none";
    document.body.classList.remove("overlay-open");
    btnOpenUxOverlay.focus();
  }

  function toggleUxOverlay() {
    if (isOverlayOpen) {
      closeUxOverlay();
    } else {
      openUxOverlay();
    }
  }

  // 5. Overlay Tab Switching Logic
  const overlayTabs = [
    { btn: tabBtnLive, panel: tabPanelLive, id: "tabPanelLive" },
    { btn: tabBtnPersonas, panel: tabPanelPersonas, id: "tabPanelPersonas" },
    { btn: tabBtnFindings, panel: tabPanelFindings, id: "tabPanelFindings" },
    { btn: tabBtnReport, panel: tabPanelReport, id: "tabPanelReport" },
  ];

  overlayTabs.forEach((tab) => {
    tab.btn.addEventListener("click", () => {
      switchOverlayTab(tab.id);
    });
  });

  function switchOverlayTab(tabId) {
    activeTabName = tabId;
    overlayTabs.forEach((tab) => {
      const isActive = tab.id === tabId;
      tab.btn.classList.toggle("active", isActive);
      tab.btn.setAttribute("aria-selected", isActive ? "true" : "false");
      tab.panel.style.display = isActive ? "block" : "none";
      tab.panel.classList.toggle("active", isActive);
    });
  }

  // 6. View Switcher (Target Website vs Automation Feed)
  btnViewWebsite.addEventListener("click", () => {
    setFullscreenView("website");
  });

  btnViewAutomation.addEventListener("click", () => {
    setFullscreenView("automation");
  });

  btnReturnToWebsite.addEventListener("click", () => {
    setFullscreenView("website");
  });

  function setFullscreenView(mode) {
    activeFullscreenView = mode;
    if (mode === "website") {
      btnViewWebsite.classList.add("active");
      btnViewAutomation.classList.remove("active");
      automationFeedLayer.style.display = "none";
    } else {
      btnViewWebsite.classList.remove("active");
      btnViewAutomation.classList.add("active");
      automationFeedLayer.style.display = "flex";
    }
  }

  // 7. Test Submission Form Handler
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
      currentTargetUrl = targetUrl;
      startFullscreenTestingView(currentRunId, targetUrl);
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

  // 8. Start Fullscreen Testing Session
  function startFullscreenTestingView(runId, url) {
    // Switch to full-screen view mode
    document.body.classList.add("mode-fullscreen");
    viewSetup.style.display = "none";
    viewFullscreenWebsite.style.display = "block";

    // Show navbar items
    navTestContext.style.display = "flex";
    btnOpenUxOverlay.style.display = "inline-flex";
    navViewToggleGroup.style.display = "inline-flex";
    btnCancelRunNav.style.display = "inline-flex";
    btnNewTestNav.style.display = "inline-flex";

    // Set Target URL link & text
    navTargetUrl.href = url;
    navTargetUrlText.textContent = url;
    overlayTargetUrl.textContent = url;

    // Load Target Website in the full-viewport iframe
    setFullscreenView("website");
    targetWebsiteIframe.src = url;

    // External link fallback
    btnExternalSite.href = url;
    if (btnExternalSite) {
      btnExternalSite.onclick = () => window.open(url, "_blank");
    }

    // Set fallback timeout check: if iframe is blocked by X-Frame-Options, show gentle notice
    frameSecurityBanner.style.display = "none";
    setTimeout(() => {
      // In cross-origin scenarios, check if user might prefer automation feed
      checkIframeFraming(url);
    }, 2500);

    // Initialize Navbar state
    updateStatusBadge("RUNNING", "badge-running");
    navPersonaName.textContent = "Synthesizing...";
    navTaskObjective.textContent = "Initializing test environment...";
    navFindingsBadge.style.display = "none";
    navFindingsBadge.textContent = "0";

    // Initialize Overlay state
    overlayRunId.textContent = runId;
    overlayMessage.textContent = "Initializing test environment...";
    livePersonaName.textContent = "Synthesizing...";
    liveTaskObjective.textContent = "Waiting for execution...";
    liveActionBadge.textContent = "[INITIALIZING]";
    liveScreenshotImg.style.display = "none";
    viewportPlaceholder.style.display = "flex";
    fullscreenScreenshotImg.style.display = "none";
    automationPlaceholder.style.display = "flex";
    eventStreamLog.innerHTML = "";
    eventCount = 0;
    eventCountBadge.textContent = "0 events";
    overlayBtnHtmlReport.style.display = "none";

    resetStepper();
    stepInspection.classList.add("step-active");
    switchOverlayTab("tabPanelLive");

    // Start timer
    timerStart = Date.now();
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      const elapsedSec = Math.floor((Date.now() - timerStart) / 1000);
      const mins = String(Math.floor(elapsedSec / 60)).padStart(2, "0");
      const secs = String(elapsedSec % 60).padStart(2, "0");
      const formatted = `${mins}:${secs}`;
      navTimer.textContent = formatted;
      overlayTimer.textContent = formatted;
    }, 1000);

    // Connect Server-Sent Events (SSE)
    connectEventSource(runId);
  }

  function checkIframeFraming(url) {
    try {
      // Test if iframe allows access or is blocked
      const isKnownRestricted = /amazon\.|google\.|github\.|twitter\.|facebook\.|x\.com/i.test(url);
      if (isKnownRestricted) {
        frameSecurityBanner.style.display = "block";
      }
    } catch (e) {
      // Security block triggered
      frameSecurityBanner.style.display = "block";
    }
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
      console.warn("EventSource disconnected or finished. Checking status fallback.");
      checkRunStatusFallback(runId);
    };
  }

  // 9. Real-Time Stream Event Handler
  function handleStreamEvent(evt) {
    eventCount++;
    eventCountBadge.textContent = `${eventCount} events`;
    appendLogEntry(evt);

    const type = evt.type || "";
    if (type === "stage_start") {
      updateStageActive(evt.stage);
      const msg = evt.message || `Starting stage: ${evt.stage}...`;
      overlayMessage.textContent = msg;
      navTaskObjective.textContent = msg;
    } else if (type === "stage_finish") {
      if (evt.stage === "inspection" && evt.screenshot_path) {
        updateViewportScreenshot(evt.screenshot_path);
      }
    } else if (type === "action_step") {
      const pName = evt.persona_name || "Active Persona";
      const taskObj = evt.task_objective || "";
      const actionName = (evt.action || "STEP").toUpperCase();

      navPersonaName.textContent = pName;
      navTaskObjective.textContent = taskObj || `Action: [${actionName}]`;
      livePersonaName.textContent = pName;
      liveTaskObjective.textContent = taskObj;
      liveActionBadge.textContent = `[${actionName}]`;

      feedPersonaText.textContent = `Persona: ${pName}`;
      feedActionText.textContent = `Action: [${actionName}] ${evt.target || ""}`;

      if (evt.screenshot_path) {
        updateViewportScreenshot(evt.screenshot_path);
      }
    } else if (type === "task_start") {
      const pName = evt.persona_name || "Active Persona";
      const taskObj = evt.task_objective || "";
      navPersonaName.textContent = pName;
      navTaskObjective.textContent = taskObj;
      livePersonaName.textContent = pName;
      liveTaskObjective.textContent = taskObj;
      liveActionBadge.textContent = "[TASK_START]";
    } else if (type === "pipeline_finish") {
      updateStatusBadge("COMPLETED", "badge-completed");
      overlayMessage.textContent = "Analysis complete! Report is ready.";
      navTaskObjective.textContent = "Test complete • Click UX Details to inspect findings";
      btnCancelRunNav.style.display = "none";
      cleanupStreaming();
      setTimeout(() => loadAndPopulateResults(currentRunId, false), 1200);
    } else if (type === "pipeline_cancelled") {
      updateStatusBadge("CANCELLED", "badge-cancelled");
      overlayMessage.textContent = "Test run was cancelled by user.";
      navTaskObjective.textContent = "Test run cancelled.";
      btnCancelRunNav.style.display = "none";
      cleanupStreaming();
    } else if (type === "pipeline_error") {
      updateStatusBadge("FAILED", "badge-failed");
      const errStr = evt.error || "Execution error encountered";
      overlayMessage.textContent = `Error: ${errStr}`;
      navTaskObjective.textContent = `Failed: ${errStr}`;
      btnCancelRunNav.style.display = "none";
      cleanupStreaming();
    }
  }

  function updateStatusBadge(text, className) {
    navStatusBadge.className = `status-badge ${className}`;
    navStatusBadge.textContent = text;
    overlayStatusBadge.className = `status-badge ${className}`;
    overlayStatusBadge.textContent = text;
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

    // Update overlay preview screenshot
    liveScreenshotImg.src = url;
    liveScreenshotImg.style.display = "block";
    viewportPlaceholder.style.display = "none";

    // Update fullscreen automation screenshot
    fullscreenScreenshotImg.src = url;
    fullscreenScreenshotImg.style.display = "block";
    automationPlaceholder.style.display = "none";
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
        updateStatusBadge("COMPLETED", "badge-completed");
        btnCancelRunNav.style.display = "none";
        loadAndPopulateResults(runId, false);
      } else if (statusData.status === "failed" || statusData.status === "cancelled") {
        cleanupStreaming();
        updateStatusBadge(statusData.status.toUpperCase(), `badge-${statusData.status}`);
        btnCancelRunNav.style.display = "none";
        overlayMessage.textContent = statusData.progress_message || statusData.error_message || "";
      }
    } catch (err) {
      console.warn("Status fallback error:", err);
    }
  }

  // 10. Cancel Run Action
  btnCancelRunNav.addEventListener("click", async () => {
    if (!currentRunId) return;
    if (!confirm("Are you sure you want to cancel the current UX testing session?")) return;

    btnCancelRunNav.disabled = true;
    try {
      await fetch(`/api/runs/${currentRunId}/cancel`, { method: "POST" });
      overlayMessage.textContent = "Cancelling test run...";
      navTaskObjective.textContent = "Cancelling test...";
    } catch (err) {
      console.error("Cancel failed:", err);
    } finally {
      btnCancelRunNav.disabled = false;
    }
  });

  // 11. Results Loading & Population inside Overlay Tabs
  async function loadAndPopulateResults(runId, autoOpenOverlay = false) {
    try {
      const resp = await fetch(`/api/runs/${runId}/results`);
      if (!resp.ok) throw new Error("Report results not ready.");
      const report = await resp.json();
      currentReportData = report;

      renderResultsIntoOverlay(report, runId);

      // Show HTML Report link button in overlay header
      overlayBtnHtmlReport.href = `/api/runs/${runId}/reports/report.html`;
      overlayBtnHtmlReport.style.display = "inline-flex";

      // If user came from history or explicitly requested, switch directly to findings tab
      if (autoOpenOverlay) {
        openUxOverlay("tabPanelFindings");
      }
    } catch (err) {
      console.error("Failed to load results:", err);
    }
  }

  function renderResultsIntoOverlay(report, runId) {
    resultWebsiteSummary.textContent = report.website_summary || "Automated analysis completed successfully.";
    btnViewHtmlReport.href = `/api/runs/${runId}/reports/report.html`;
    btnDownloadJsonReport.href = `/api/runs/${runId}/reports/report.json`;

    // Metrics KPIs
    const metrics = report.task_metrics || {};
    metricTasksPassed.textContent = `${metrics.passed_tasks || 0} / ${metrics.total_tasks || 0}`;
    metricTasksSub.textContent = `${metrics.failed_tasks || 0} failures, ${metrics.inconclusive_tasks || 0} inconclusive`;

    metricVerifiedIssues.textContent = report.verified_issues_count || 0;
    metricUsabilityObservations.textContent = report.usability_observations_count || 0;
    metricPotentialImprovements.textContent = report.potential_improvements_count || 0;

    // Findings count badge on Navbar Button
    const findings = report.findings || [];
    const totalFindings = findings.length;
    tabCountFindings.textContent = totalFindings;

    if (totalFindings > 0) {
      navFindingsBadge.textContent = totalFindings;
      navFindingsBadge.style.display = "inline-block";
    }

    // Filter tab counts
    countTabAll.textContent = totalFindings;
    countTabVerified.textContent = findings.filter(f => f.category === "OBJECTIVE_DEFECT").length;
    countTabUsability.textContent = findings.filter(f => f.category === "USABILITY_OBSERVATION").length;
    countTabImprovement.textContent = findings.filter(f => f.category === "POTENTIAL_IMPROVEMENT").length;

    // Render Personas inside Tab 2
    resultsPersonasContainer.innerHTML = "";
    const personasList = report.personas_summary || report.persona_summaries || [];
    tabCountPersonas.textContent = personasList.length;

    if (personasList.length === 0) {
      resultsPersonasContainer.innerHTML = `<div class="dim" style="padding: 2rem; text-align: center;">No simulated personas recorded for this run.</div>`;
    } else {
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
    }

    renderFindingsList();
  }

  // 12. Filter Tabs for Findings in Overlay Tab 3
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
    if (!currentReportData || !currentReportData.findings) {
      resultsFindingsList.innerHTML = `<div class="dim" style="padding: 2rem; text-align: center;">No findings recorded yet.</div>`;
      return;
    }

    const filtered = currentReportData.findings.filter((f) => {
      if (currentFilterCategory === "ALL") return true;
      return f.category === currentFilterCategory;
    });

    if (filtered.length === 0) {
      resultsFindingsList.innerHTML = `<div class="dim" style="padding: 2rem; text-align: center;">No findings in this category.</div>`;
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

  // 13. Past Runs History Modal Logic
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
        btnView.textContent = "View in Studio";
        btnView.addEventListener("click", () => {
          historyModal.style.display = "none";
          currentRunId = r.run_id;
          currentTargetUrl = r.target_url;
          startFullscreenTestingView(r.run_id, r.target_url);
          loadAndPopulateResults(r.run_id, true);
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

  // 14. Reset to Setup View Logic
  function resetToSetup() {
    cleanupStreaming();
    closeUxOverlay();

    document.body.classList.remove("mode-fullscreen");
    viewFullscreenWebsite.style.display = "none";
    viewSetup.style.display = "block";

    navTestContext.style.display = "none";
    btnOpenUxOverlay.style.display = "none";
    navViewToggleGroup.style.display = "none";
    btnCancelRunNav.style.display = "none";
    btnNewTestNav.style.display = "none";
    targetWebsiteIframe.src = "about:blank";

    currentRunId = null;
    currentTargetUrl = "";
    currentReportData = null;

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
