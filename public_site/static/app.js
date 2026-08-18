const form = document.querySelector("#repair-form");
const chartInput = document.querySelector("#chart");
const promptInput = document.querySelector("#prompt");
const promptCount = document.querySelector("#prompt-count");
const preview = document.querySelector("#upload-preview");
const dropZone = document.querySelector("#drop-zone");
const submitButton = document.querySelector("#submit-button");
const statusPanel = document.querySelector("#status-panel");
const statusTitle = document.querySelector("#status-title");
const statusCopy = document.querySelector("#status-copy");
const results = document.querySelector("#results");
const originalResult = document.querySelector("#original-result");
const repairedResult = document.querySelector("#repaired-result");
const downloadLink = document.querySelector("#download-link");
const reviewNote = document.querySelector("#review-note");
const retryForm = document.querySelector("#retry-form");
const feedbackInput = document.querySelector("#feedback");
const retryButton = document.querySelector("#retry-button");
const retryNote = document.querySelector("#retry-note");
const newChartButton = document.querySelector("#new-chart-button");
const errorPanel = document.querySelector("#error-panel");
const errorCopy = document.querySelector("#error-copy");
const errorReset = document.querySelector("#error-reset");

let currentCaseId = null;
let previewUrl = null;
let pollTimer = null;

promptInput.addEventListener("input", () => {
  promptCount.textContent = String(promptInput.value.length);
});

function showSelectedFile(file) {
  if (!file) return;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(file);
  preview.src = previewUrl;
  preview.hidden = false;
  dropZone.classList.add("has-image");
}

chartInput.addEventListener("change", () => showSelectedFile(chartInput.files[0]));

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragging");
  });
});

dropZone.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files[0];
  if (!file) return;
  const transfer = new DataTransfer();
  transfer.items.add(file);
  chartInput.files = transfer.files;
  showSelectedFile(file);
});

function setProcessing(title, copy) {
  results.hidden = true;
  errorPanel.hidden = true;
  statusTitle.textContent = title;
  statusCopy.textContent = copy;
  statusPanel.hidden = false;
}

function showError(message) {
  window.clearTimeout(pollTimer);
  statusPanel.hidden = true;
  results.hidden = true;
  errorCopy.textContent = message || "Please try again with a different image.";
  errorPanel.hidden = false;
  submitButton.disabled = false;
}

async function readJson(response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "Something went wrong");
  return body;
}

function pollCase(caseId) {
  window.clearTimeout(pollTimer);
  pollTimer = window.setTimeout(async () => {
    try {
      const data = await readJson(await fetch(`/api/cases/${caseId}`, { cache: "no-store" }));
      if (data.status === "ready") {
        renderResult(data);
      } else if (data.status === "failed") {
        showError(data.error || "The repair did not finish.");
      } else {
        pollCase(caseId);
      }
    } catch (error) {
      showError(error.message);
    }
  }, 2200);
}

function renderResult(data) {
  window.clearTimeout(pollTimer);
  statusPanel.hidden = true;
  errorPanel.hidden = true;
  originalResult.src = `${data.original_url}?v=${Date.now()}`;
  repairedResult.src = `${data.repaired_url}?v=${Date.now()}`;
  downloadLink.href = data.download_url;

  if (data.review?.verdict === "Retry") {
    const required = data.review.required_changes?.[0];
    reviewNote.textContent = required
      ? `The reviewer suggests one more pass: ${required} Values may be approximate.`
      : "The reviewer suggests one more pass. Values may be approximate.";
  } else {
    reviewNote.textContent = data.values_note;
  }

  retryForm.hidden = !data.can_retry;
  retryButton.disabled = false;
  feedbackInput.disabled = false;
  feedbackInput.value = "";
  retryNote.textContent = data.can_retry
    ? "You get one retry for this chart."
    : "The retry for this chart has been used.";
  submitButton.disabled = false;
  results.hidden = false;
  results.scrollIntoView({ behavior: "smooth", block: "start" });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!chartInput.files[0]) return;
  submitButton.disabled = true;
  const data = new FormData(form);
  setProcessing("Rebuilding the chart", "This usually takes a couple of minutes.");
  try {
    const created = await readJson(await fetch("/api/cases", { method: "POST", body: data }));
    currentCaseId = created.case_id;
    pollCase(currentCaseId);
  } catch (error) {
    showError(error.message);
  }
});

retryForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const feedback = feedbackInput.value.trim();
  if (!feedback || !currentCaseId) return;
  retryButton.disabled = true;
  feedbackInput.disabled = true;
  const data = new FormData();
  data.set("feedback", feedback);
  setProcessing("Trying that change", "I’m keeping the current chart and changing only what you asked for.");
  try {
    await readJson(await fetch(`/api/cases/${currentCaseId}/retry`, { method: "POST", body: data }));
    pollCase(currentCaseId);
  } catch (error) {
    showError(error.message);
  }
});

function resetPage() {
  window.clearTimeout(pollTimer);
  currentCaseId = null;
  form.reset();
  promptCount.textContent = "0";
  preview.hidden = true;
  preview.removeAttribute("src");
  dropZone.classList.remove("has-image");
  statusPanel.hidden = true;
  results.hidden = true;
  errorPanel.hidden = true;
  submitButton.disabled = false;
  document.querySelector("#intro").scrollIntoView({ behavior: "smooth", block: "start" });
}

newChartButton.addEventListener("click", resetPage);
errorReset.addEventListener("click", resetPage);
