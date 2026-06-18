// Red-team service debug UI.
//
// This small browser script powers the standalone FastAPI red-team page at
// `red_teaming/app/main.py`. It starts runs, refreshes run state, renders case
// scores, and submits optional human review overrides. The main React frontend
// uses its own red-team interface; this file is kept as a lightweight service
// console for local debugging.

const runsNode = document.getElementById("runs");
const detailNode = document.getElementById("run-detail");
const startButton = document.getElementById("start-run");
const refreshButton = document.getElementById("refresh-runs");

let selectedRunId = null;

function pct(value) {
  if (value === null || value === undefined) return "n/a";
  return `${Math.round(Number(value) * 100)}%`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function jsonFetch(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`${response.status}: ${await response.text()}`);
  }
  return response.json();
}

async function loadRuns() {
  const payload = await jsonFetch("/api/runs");
  runsNode.innerHTML = payload.runs.map(run => `
    <article class="run-card" data-run-id="${run.run_id}">
      <strong>${escapeHtml(run.run_id)}</strong>
      <p class="meta">${escapeHtml(run.status)} · ${escapeHtml(run.profile_label || "profile pending")}</p>
      <span class="pill">overall ${pct(run.overall_score)}</span>
      <span class="pill">pending ${run.pending_human_reviews ?? "n/a"}</span>
    </article>
  `).join("") || `<p class="empty">No runs yet.</p>`;
  document.querySelectorAll(".run-card").forEach(card => {
    card.addEventListener("click", () => loadRun(card.dataset.runId));
  });
}

function renderScores(scores) {
  const methodScores = scores?.method_scores || {};
  const cards = [
    ["Overall", scores?.overall_score],
    ...Object.entries(methodScores),
  ];
  return `
    <div class="scores">
      ${cards.map(([label, value]) => `
        <div class="score-card">
          <span class="small">${escapeHtml(label)}</span>
          <strong>${pct(value)}</strong>
        </div>
      `).join("")}
    </div>
    <p class="small">
      Pending human reviews: ${scores?.pending_human_reviews ?? 0}.
      Completed human reviews: ${scores?.completed_human_reviews ?? 0}.
      Finalized: ${scores?.is_final ? "yes" : "no"}.
    </p>
  `;
}

function renderLlmGrade(caseItem) {
  const grade = caseItem.llm_grade;
  if (!grade) return "";
  if (!grade.available) {
    return `<div class="llm-grade unavailable"><strong>LLM judge unavailable</strong><p>${escapeHtml(grade.error || "No grade captured.")}</p></div>`;
  }
  const indicators = Array.isArray(grade.indicators) ? grade.indicators : [];
  return `
    <div class="llm-grade">
      <p><strong>LLM judge:</strong> ${pct(grade.score)} · confidence ${pct(grade.confidence)} · ${escapeHtml(grade.primary_failure || "none")}</p>
      ${grade.score_reason ? `<p><strong>Score reason:</strong> ${escapeHtml(grade.score_reason)}</p>` : ""}
      <p>${escapeHtml(grade.rationale || "")}</p>
      ${indicators.length ? `<ul>${indicators.map(item => `
        <li><strong>${escapeHtml(item.name || "indicator")}:</strong> ${escapeHtml(item.result || "mixed")} ${escapeHtml(item.evidence || "")}</li>
      `).join("")}</ul>` : ""}
    </div>
  `;
}

function renderCase(caseItem) {
  const review = caseItem.human_review || {};
  const reasons = (caseItem.automated_reasons || []).map(escapeHtml).join("<br>");
  return `
    <article class="case-card">
      <h3>${escapeHtml(caseItem.prompt_id)} · ${escapeHtml(caseItem.method_name)}</h3>
      <div class="case-grid">
        <div>
          <p class="small">Prompt</p>
          <p class="case-text">${escapeHtml(caseItem.message)}</p>
          <br>
          ${caseItem.expected_answer ? `
            <p class="small">Expected answer behavior</p>
            <p class="expected-answer">${escapeHtml(caseItem.expected_answer)}</p>
            <br>
          ` : ""}
          <p class="small">Response</p>
          <p class="case-text">${escapeHtml(caseItem.response_text)}</p>
          <br>
          <span class="pill">auto ${pct(caseItem.automated_score)}</span>
          ${caseItem.rule_score !== undefined ? `<span class="pill">rule ${pct(caseItem.rule_score)}</span>` : ""}
          ${caseItem.llm_score !== undefined && caseItem.llm_score !== null ? `<span class="pill">LLM ${pct(caseItem.llm_score)}</span>` : ""}
          <span class="pill">human needed ${caseItem.needs_human_review ? "yes" : "no"}</span>
          ${renderLlmGrade(caseItem)}
          <p class="small">${reasons}</p>
        </div>
        <form class="review-form" data-case-id="${caseItem.case_id}">
          <label>
            Human score 0-1
            <input name="score" type="number" min="0" max="1" step="0.05" value="${review.score ?? caseItem.automated_score ?? 0.5}">
          </label>
          <p class="derived-result">Derived result: ${Number(review.score ?? caseItem.automated_score ?? 0.5) >= 0.5 ? "Pass" : "Fail"}</p>
          <label>
            Notes
            <textarea name="notes">${escapeHtml(review.notes || "")}</textarea>
          </label>
          <button type="submit">Save human review</button>
        </form>
      </div>
    </article>
  `;
}

function renderGroupedCases(cases) {
  const groups = cases.reduce((acc, caseItem) => {
    const key = caseItem.method || "Other";
    if (!acc[key]) {
      acc[key] = {
        title: caseItem.method_name || key,
        items: [],
      };
    }
    acc[key].items.push(caseItem);
    return acc;
  }, {});
  return Object.values(groups).map(group => `
    <section class="case-group">
      <h2>${escapeHtml(group.title)}</h2>
      ${group.items.map(renderCase).join("")}
    </section>
  `).join("");
}

async function loadRun(runId) {
  selectedRunId = runId;
  const run = await jsonFetch(`/api/runs/${runId}`);
  const reviewPayload = await jsonFetch(`/api/runs/${runId}/review-items`);
  const completed = run.cases.filter(item => item.status === "completed").length;
  detailNode.innerHTML = `
    <h2>${escapeHtml(run.run_id)}</h2>
    <p class="meta">${escapeHtml(run.status)} · ${completed}/${run.cases.length} cases completed</p>
    <p class="meta">Profile: ${escapeHtml(run.profile?.label || "pending")} ${escapeHtml(run.profile?.id || "")}</p>
    ${renderScores(run.final_scores)}
    <h2>Human Review Queue</h2>
    ${renderGroupedCases(reviewPayload.cases) || `<p class="empty">No review items yet.</p>`}
  `;
  document.querySelectorAll(".review-form").forEach(form => {
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const data = new FormData(form);
      await jsonFetch(`/api/runs/${selectedRunId}/review-items/${form.dataset.caseId}`, {
        method: "POST",
        body: JSON.stringify({
          score: Number(data.get("score")),
          notes: data.get("notes") || "",
        }),
      });
      await loadRun(selectedRunId);
      await loadRuns();
    });
  });
}

startButton.addEventListener("click", async () => {
  const seedValue = document.getElementById("seed").value;
  const selectedMethods = Array.from(document.querySelectorAll(".method-option:checked")).map(input => input.value);
  const targetMode = document.querySelector("input[name='target-mode']:checked")?.value || "guardrailed";
  const payload = await jsonFetch("/api/runs", {
    method: "POST",
    body: JSON.stringify({
      backend_url: document.getElementById("backend-url").value,
      country: document.getElementById("country").value,
      seed: seedValue ? Number(seedValue) : null,
      selected_methods: selectedMethods.length ? selectedMethods : null,
      target_mode: targetMode,
    }),
  });
  await loadRuns();
  await loadRun(payload.run_id);
});

refreshButton.addEventListener("click", async () => {
  await loadRuns();
  if (selectedRunId) await loadRun(selectedRunId);
});

loadRuns();
setInterval(async () => {
  if (document.activeElement?.closest?.(".review-form")) return;
  await loadRuns();
  if (selectedRunId) await loadRun(selectedRunId);
}, 8000);
