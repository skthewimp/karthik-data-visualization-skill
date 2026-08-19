let selectedChart = null;
let currentCase = null;
let runnerAvailable = false;
let activeJob = null;

const $ = (selector) => document.querySelector(selector);

async function api(url, options = {}) {
  const response = await fetch(url, options);
  let payload;
  try {
    payload = await response.json();
  } catch {
    payload = { detail: await response.text() };
  }
  if (!response.ok) throw new Error(payload.detail || "Request failed");
  return payload;
}

function setSelectedChart(file) {
  if (!file || !["image/png", "image/jpeg"].includes(file.type)) {
    $("#start-error").textContent = "Choose a PNG or JPEG image.";
    return;
  }
  selectedChart = file;
  const preview = $("#intake-preview");
  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
  $("#drop-copy").hidden = true;
  $("#start-error").textContent = "";
}

function formObject(form) {
  return Object.fromEntries(
    [...new FormData(form).entries()].filter(([, value]) => String(value).trim() !== "")
  );
}

function renderCase(data) {
  currentCase = data;
  $("#intake").hidden = true;
  $("#workspace").hidden = false;
  $("#case-id").textContent = data.case_id;
  $("#case-state").textContent = data.state.replaceAll("_", " ");
  $("#context-version").textContent = `context v${data.context_version}`;
  $("#iteration-budget").textContent = data.budget_status.iterations_remaining === null
    ? "No iteration cap"
    : `${data.budget_status.iterations_remaining} iterations left`;
  $("#cost-budget").textContent = `$${Number(data.budget_status.cost_usd).toFixed(3)} used`;
  $("#token-budget").textContent = `${Number(data.budget_status.tokens_used).toLocaleString()} tokens used`;

  const stamp = `?v=${Date.now()}`;
  $("#original-artifact").src = data.artifact_urls.original + stamp;
  renderArtifact("latest", data.artifact_urls.latest, data.iterations.length ? `iteration ${data.iterations.at(-1).number}` : "Not uploaded");
  renderArtifact("best", data.artifact_urls.best, data.best_candidate ? `iteration ${data.best_candidate.iteration}` : "None yet");

  const fields = data.context.fields;
  for (const name of ["audience", "purpose", "question", "hypothesis", "message", "medium", "dimensions", "preserve"]) {
    const input = $(`#context-form [name="${name}"]`);
    if (input) input.value = fields[name]?.value || "";
  }
  $('#limits-form [name="max_iterations"]').value = data.limits.max_iterations || "";
  $('#limits-form [name="max_cost_usd"]').value = data.limits.max_cost_usd || "";
  $('#limits-form [name="max_tokens"]').value = data.limits.max_tokens || "";
  $("#stop-button").disabled = ["blocked", "stopped", "accepted", "accepted_with_override"].includes(data.state);
  $("#resume-button").disabled = !["blocked", "stopped"].includes(data.state);
  updateRunButton();
  renderHistory(data.transitions);
}

function updateRunButton() {
  const runnable = currentCase && ["critique", "design", "build", "revise", "redesign"].includes(currentCase.state);
  $("#run-button").disabled = !runnerAvailable || !runnable || Boolean(activeJob);
}

function renderArtifact(kind, url, label) {
  const img = $(`#${kind}-artifact`);
  const frame = $(`#${kind}-frame`);
  $(`#${kind}-label`).textContent = label;
  if (url) {
    img.src = url + `?v=${Date.now()}`;
    img.hidden = false;
    frame.classList.remove("empty");
  } else {
    img.hidden = true;
    frame.classList.add("empty");
  }
}

function renderHistory(transitions) {
  const rows = transitions
    .slice()
    .reverse()
    .map(
      (item) => `
        <div class="history-row">
          <code>${escapeHtml(item.from ?? "start")} → ${escapeHtml(item.to)}</code>
          <span>${escapeHtml(item.action)}</span>
          <span>${escapeHtml(item.reason)}</span>
        </div>`
    )
    .join("");
  $("#history").innerHTML = `<div class="history-list">${rows}</div>`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function refreshCase() {
  if (!currentCase) return;
  renderCase(await api(`/api/cases/${currentCase.case_id}`));
}

async function loadRunnerStatus() {
  try {
    const health = await api("/api/health");
    runnerAvailable = health.provider_runner;
    $("#runner-heading").textContent = runnerAvailable ? "Local Codex runner enabled" : "Manual case-console mode";
    $("#runner-copy").textContent = runnerAvailable
      ? "Each click runs one creator pass and one fresh reviewer pass against the checked-out skills."
      : "Set DATAVIZ_ENABLE_LOCAL_RUNNER=1 and restart to connect the local Codex client.";
    $("#run-status").textContent = runnerAvailable
      ? `Ready: ${health.model}; ${health.run_scope}.${health.estimated_cycle_tokens ? ` Measured estimate: ${Number(health.estimated_cycle_tokens).toLocaleString()} tokens.` : " No measured token estimate yet."}`
      : "Local model runner is not enabled.";
    updateRunButton();
  } catch (error) {
    $("#runner-heading").textContent = "Runner status unavailable";
    $("#runner-copy").textContent = error.message;
  }
}

async function pollJob(jobId) {
  try {
    while (activeJob === jobId) {
      const job = await api(`/api/jobs/${jobId}`);
      const latest = job.events.at(-1);
      $("#run-status").textContent = latest ? `${latest.stage}: ${latest.message}` : job.status;
      if (["complete", "failed"].includes(job.status)) {
        activeJob = null;
        await refreshCase();
        if (job.error) throw new Error(job.error);
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  } catch (error) {
    activeJob = null;
    updateRunButton();
    showWorkspaceError(error);
  }
}

function showWorkspaceError(error) {
  $("#workspace-error").textContent = error.message;
}

const dropZone = $("#drop-zone");
dropZone.addEventListener("click", () => $("#chart-file").click());
dropZone.addEventListener("keydown", (event) => {
  if (["Enter", " "].includes(event.key)) $("#chart-file").click();
});
dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropZone.classList.add("dragging");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragging"));
dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropZone.classList.remove("dragging");
  setSelectedChart(event.dataTransfer.files[0]);
});
$("#chart-file").addEventListener("change", (event) => setSelectedChart(event.target.files[0]));
document.addEventListener("paste", (event) => {
  const file = [...event.clipboardData.items]
    .find((item) => item.type.startsWith("image/"))
    ?.getAsFile();
  if (file && !currentCase) setSelectedChart(file);
});

$("#start-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!selectedChart) {
    $("#start-error").textContent = "Paste or choose a chart first.";
    return;
  }
  const button = event.submitter;
  button.disabled = true;
  try {
    const data = new FormData(event.currentTarget);
    data.set("chart", selectedChart, selectedChart.name || "pasted-chart.png");
    renderCase(await api("/api/cases", { method: "POST", body: data }));
  } catch (error) {
    $("#start-error").textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

$("#context-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = formObject(event.currentTarget);
    renderCase(
      await api(`/api/cases/${currentCase.case_id}/context`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
    );
    event.currentTarget.elements.text.value = "";
  } catch (error) {
    showWorkspaceError(error);
  }
});

$("#feedback-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    renderCase(
      await api(`/api/cases/${currentCase.case_id}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formObject(event.currentTarget)),
      })
    );
    event.currentTarget.reset();
  } catch (error) {
    showWorkspaceError(error);
  }
});

$("#iteration-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    renderCase(
      await api(`/api/cases/${currentCase.case_id}/iterations`, {
        method: "POST",
        body: new FormData(event.currentTarget),
      })
    );
    event.currentTarget.reset();
  } catch (error) {
    showWorkspaceError(error);
  }
});

$("#run-button").addEventListener("click", async () => {
  $("#workspace-error").textContent = "";
  try {
    const job = await api(`/api/cases/${currentCase.case_id}/run`, { method: "POST" });
    activeJob = job.job_id;
    $("#run-status").textContent = "Queued one creator + reviewer cycle.";
    updateRunButton();
    pollJob(activeJob);
  } catch (error) {
    showWorkspaceError(error);
  }
});

$("#limits-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const raw = formObject(event.currentTarget);
    const payload = Object.fromEntries(Object.entries(raw).map(([key, value]) => [key, Number(value)]));
    renderCase(
      await api(`/api/cases/${currentCase.case_id}/limits`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
    );
  } catch (error) {
    showWorkspaceError(error);
  }
});

$("#stop-button").addEventListener("click", async () => {
  try {
    renderCase(
      await api(`/api/cases/${currentCase.case_id}/stop`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind: "user_stop", reason: "Stopped from the local tester" }),
      })
    );
  } catch (error) {
    showWorkspaceError(error);
  }
});

$("#resume-button").addEventListener("click", async () => {
  try {
    renderCase(
      await api(`/api/cases/${currentCase.case_id}/resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "Resumed from the local tester" }),
      })
    );
  } catch (error) {
    showWorkspaceError(error);
  }
});

$("#refresh-button").addEventListener("click", refreshCase);
loadRunnerStatus();
