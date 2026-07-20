const priorityKey = "greenSpectrum.priority.v1";
const impactKey = "greenSpectrum.impactJourney.v1";
const exploreKey = "greenSpectrum.explore.v1";
const onboardingKey = "greenSpectrum.onboarding.v1";
const sessionKey = "greenSpectrum.sessionId.v1";

const onboardingPriority = JSON.parse(localStorage.getItem(onboardingKey) || "{}");
const impactData = JSON.parse(localStorage.getItem(impactKey) || "{}");
const exploreData = JSON.parse(localStorage.getItem(exploreKey) || "{}");
const savedPriority = JSON.parse(localStorage.getItem(priorityKey) || "{}");
const priorityAnonymousSessionId = localStorage.getItem(sessionKey) || `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
localStorage.setItem(sessionKey, priorityAnonymousSessionId);
let priorityBackendReady = false;

const spectrumLevels = ["white", "light", "mid", "dark", "unsure"];
const cynefinDomains = ["clear", "complicated", "complex", "chaotic", "confused", "mixed"];
const defaultWeights = {
  impact: 20,
  strategic: 15,
  leverage: 15,
  urgency: 10,
  influence: 10,
  readiness: 10,
  confidence: 10,
  stakeholder: 5,
  learning: 5,
  effort: 10
};

const priorityState = {
  stateId: savedPriority.stateId || "",
  sourceImpactJourneyStateId: savedPriority.sourceImpactJourneyStateId || impactData.stateId || "",
  problems: savedPriority.problems || importProblems(),
  weights: savedPriority.weights || defaultWeights,
  selectedIds: savedPriority.selectedIds || [],
  reviewed: savedPriority.reviewed || false
};

document.querySelector("[data-priority-organisation]").textContent = onboardingPriority.organisationName || "New journey";
window.greenSpectrumEvents = window.greenSpectrumEvents || [];
window.greenSpectrumEvents.push({ eventName: "prioritisation_started", at: new Date().toISOString() });
initialisePriority();
hydratePriorityFromBackend();

function initialisePriority() {
  priorityState.problems = priorityState.problems.map(enrichProblem);
  renderAll();
  restoreReview();
}

function importProblems() {
  const problems = [];
  Object.values(exploreData.responses || {})
    .filter((response) => ["white", "light", "unknown"].includes(response.maturity))
    .slice(0, 8)
    .forEach((response, index) => {
      problems.push({
        id: `explore-${response.id || index}`,
        title: `${response.area || "Explore finding"} needs attention`,
        description: `${response.area || "This area"} appears underdeveloped or uncertain because the Explore response was ${response.maturity || "low confidence"}, leading to a need for comparison before action.`,
        source: "Explore and Map",
        confidence: confidenceNumber(response.confidence),
        status: "unreviewed",
        cluster: clusterFromText(response.area || ""),
        evidence: response.evidence || "Explore response",
        relatedStages: [],
        userEdited: false
      });
    });
  (impactData.problemSignals || []).forEach((signal, index) => {
    problems.push({
      id: `impact-${signal.id || index}`,
      title: signal.title || "Impact Journey signal",
      description: signal.description || "Mapped system issue requiring prioritisation.",
      source: "Impact Journey",
      confidence: confidenceNumber(signal.confidence),
      status: "unreviewed",
      cluster: clusterFromText(`${signal.title} ${signal.description}`),
      evidence: signal.source || "Impact Journey map",
      relatedStages: signal.stageIds || [],
      userEdited: false
    });
  });
  if (!problems.length) {
    [
      "Supplier sustainability expectations exist because traceability and evidence remain incomplete, leading to weak Scope 3 confidence and delayed decisions.",
      "Packaging waste remains high because product design and end-of-life ownership are disconnected, leading to avoidable material loss.",
      "Sustainability governance exists because accountability is not linked to operational decision points, leading to inconsistent delivery.",
      "Employee engagement is uneven because sustainability responsibilities are unclear, leading to low participation and missed learning.",
      "Data ownership is fragmented because systems are managed across separate teams, leading to slow reporting and weak prioritisation."
    ].forEach((description, index) => {
      problems.push({
        id: `demo-${index + 1}`,
        title: description.split(" because ")[0],
        description,
        source: "System-generated demo",
        confidence: index === 0 ? 3 : 2,
        status: "unreviewed",
        cluster: clusterFromText(description),
        evidence: "Prototype placeholder",
        relatedStages: [],
        userEdited: false
      });
    });
  }
  return problems;
}

function enrichProblem(problem) {
  const text = `${problem.title} ${problem.description} ${problem.cluster}`.toLowerCase();
  const base = {
    spectrum: problem.spectrum || suggestSpectrum(text),
    cynefin: problem.cynefin || suggestCynefin(text, problem),
    scores: problem.scores || suggestScores(text, problem),
    archetypes: problem.archetypes || [],
    selected: priorityState.selectedIds.includes(problem.id)
  };
  const enriched = { ...problem, ...base };
  enriched.overall = calculateScore(enriched);
  enriched.archetypes = assignArchetypes(enriched);
  return enriched;
}

function renderAll() {
  priorityState.problems = priorityState.problems.map((problem) => ({ ...problem, overall: calculateScore(problem), archetypes: assignArchetypes(problem) }));
  renderOrientation();
  renderProblemList();
  renderDuplicates();
  renderClassifications();
  renderScores();
  renderCriteria();
  renderMatrices();
  renderHeatmaps();
  renderRecommendations();
  renderSelection();
  renderPathways();
  renderDashboard();
  updatePriorityProgress();
  savePriority();
}

function renderOrientation() {
  const sources = countBy(priorityState.problems, "source");
  const cards = document.querySelector("[data-source-cards]");
  if (cards) {
    cards.innerHTML = [
      ["Explore and Map", "Problems discovered through Business, Human and Planetary maturity assessment.", sources["Explore and Map"] || 0],
      ["Impact Journey", "Problems discovered across activities, impacts, stakeholders, evidence gaps and system relationships.", sources["Impact Journey"] || 0],
      ["User-added signals", "Additional concerns entered manually.", sources["User-created"] || 0],
      ["System-generated connections", "Problems inferred from repeated patterns, contradictions or dependencies.", sources["System-generated demo"] || 0]
    ].map(([title, copy, metric]) => `<article class="info-card reveal is-visible"><h3>${title}</h3><p>${copy}</p><strong>${metric} signals</strong></article>`).join("");
  }
  const duplicates = duplicatePairs().length;
  const lowConfidence = priorityState.problems.filter((p) => p.confidence <= 2).length;
  const quickWins = priorityState.problems.filter((p) => p.archetypes.includes("quick-win")).length;
  setHtml("[data-dynamic-summary]", `
    <span>${priorityState.problems.length} problem signals imported</span>
    <span>${duplicates} likely duplicates</span>
    <span>${lowConfidence} low-confidence signals</span>
    <span>${priorityState.problems.filter((p) => p.archetypes.includes("system-leverage-point")).length} cross-system problems</span>
    <span>${quickWins} likely quick wins</span>
  `);
}

function renderProblemList() {
  const target = document.querySelector("[data-problem-list]");
  if (!target) return;
  const search = (document.querySelector("[data-problem-search]")?.value || "").toLowerCase();
  const filter = document.querySelector("[data-problem-filter]")?.value || "all";
  const sort = document.querySelector("[data-problem-sort]")?.value || "score";
  let items = priorityState.problems.filter((problem) => {
    const matchesSearch = !search || `${problem.title} ${problem.description} ${problem.evidence}`.toLowerCase().includes(search);
    const matchesFilter = filter === "all" || problem.status === filter || (filter === "selected" && priorityState.selectedIds.includes(problem.id));
    return matchesSearch && matchesFilter;
  });
  items = sortProblems(items, sort);
  target.innerHTML = items.map(problemCard).join("");
}

function problemCard(problem) {
  return `
    <article class="priority-problem-card" data-problem="${problem.id}">
      <div>
        <span class="confidence-badge">${problem.source} · ${problem.status}</span>
        <h3 contenteditable="true" data-problem-field="title">${escapeHtml(problem.title)}</h3>
        <p contenteditable="true" data-problem-field="description">${escapeHtml(problem.description)}</p>
      </div>
      <dl>
        <div><dt>Evidence</dt><dd>${escapeHtml(problem.evidence || "Missing")}</dd></div>
        <div><dt>Confidence</dt><dd>${problem.confidence}/5</dd></div>
        <div><dt>Cluster</dt><dd>${problem.cluster}</dd></div>
        <div><dt>Score</dt><dd>${problem.overall}</dd></div>
      </dl>
      <div class="problem-actions">
        <button type="button" data-status="confirmed">Confirm</button>
        <button type="button" data-status="research">Mark for research</button>
        <button type="button" data-status="archived">Archive</button>
        <button type="button" data-select-problem>${priorityState.selectedIds.includes(problem.id) ? "Remove selection" : "Select for focus"}</button>
      </div>
    </article>
  `;
}

function renderDuplicates() {
  const pairs = duplicatePairs();
  setHtml("[data-duplicate-list]", pairs.length ? pairs.map(([a, b]) => `
    <article class="duplicate-card">
      <div><h3>${escapeHtml(a.title)}</h3><p>${escapeHtml(a.description)}</p></div>
      <div><h3>${escapeHtml(b.title)}</h3><p>${escapeHtml(b.description)}</p></div>
      <div class="hero-actions"><button class="button button-secondary" type="button" data-merge="${a.id}|${b.id}">Merge</button><button class="button button-secondary" type="button">Keep separate</button><button class="button button-secondary" type="button">Link as related</button></div>
    </article>
  `).join("") : "<p>No likely duplicates found. You can still refine problem wording in the portfolio cards.</p>");
  setHtml("[data-quality-flags]", priorityState.problems.map((problem) => {
    const flags = qualityFlags(problem);
    return `<article class="quality-row"><strong>${escapeHtml(problem.title)}</strong><span>${flags.join(", ")}</span></article>`;
  }).join(""));
}

function renderClassifications() {
  renderSpectrum();
  renderCynefin();
  setHtml("[data-spectrum-list]", priorityState.problems.filter((p) => p.status !== "archived").map((problem) => classificationRow(problem, "spectrum", spectrumLevels)).join(""));
  setHtml("[data-complexity-list]", priorityState.problems.filter((p) => p.status !== "archived").map((problem) => classificationRow(problem, "cynefin", cynefinDomains)).join(""));
}

function classificationRow(problem, field, options) {
  const label = field === "spectrum" ? "Green Spectrum" : "Cynefin";
  return `
    <article class="classification-row" data-problem="${problem.id}">
      <div><h3>${escapeHtml(problem.title)}</h3><p>${classificationRationale(problem, field)}</p></div>
      <label>${label} classification
        <select data-classification="${field}">
          ${options.map((option) => `<option value="${option}" ${problem[field] === option ? "selected" : ""}>${titleCase(option)}</option>`).join("")}
        </select>
      </label>
    </article>
  `;
}

function renderSpectrum() {
  const target = document.querySelector("[data-spectrum-visual]");
  if (!target) return;
  target.innerHTML = ["white", "light", "mid", "dark", "unsure"].map((level) => `
    <div class="spectrum-lane ${level}">
      <h3>${titleCase(level)}</h3>
      ${priorityState.problems.filter((p) => p.spectrum === level && p.status !== "archived").map((p) => `<button type="button" data-focus-problem="${p.id}">${escapeHtml(p.title)}</button>`).join("") || "<span>No problems</span>"}
    </div>
  `).join("");
}

function renderCynefin() {
  const target = document.querySelector("[data-cynefin-map]");
  if (!target) return;
  target.innerHTML = cynefinDomains.map((domain) => `
    <div class="cynefin-domain ${domain}">
      <h3>${titleCase(domain)}</h3>
      ${priorityState.problems.filter((p) => p.cynefin === domain && p.status !== "archived").map((p) => `<button type="button" data-focus-problem="${p.id}">${escapeHtml(p.title)}</button>`).join("") || "<span>No problems</span>"}
    </div>
  `).join("");
}

function renderScores() {
  const target = document.querySelector("[data-score-editor]");
  if (!target) return;
  target.innerHTML = priorityState.problems.filter((p) => p.status !== "archived").map((problem) => `
    <article class="score-card" data-problem="${problem.id}">
      <h3>${escapeHtml(problem.title)}</h3>
      <div class="score-grid">
        ${["impact", "effort", "strategic", "urgency", "confidence", "readiness", "influence", "leverage", "stakeholder", "learning"].map((key) => scoreControl(problem, key)).join("")}
      </div>
    </article>
  `).join("");
}

function scoreControl(problem, key) {
  return `<label>${titleCase(key)} <input type="range" min="1" max="5" value="${problem.scores[key] || 3}" data-score="${key}"><span>${problem.scores[key] || 3}</span></label>`;
}

function renderCriteria() {
  const target = document.querySelector("[data-criteria-list]");
  if (!target) return;
  target.innerHTML = Object.entries(priorityState.weights).map(([key, weight]) => `
    <label class="weight-row">${titleCase(key)} <input type="range" min="0" max="30" value="${weight}" data-weight="${key}"><span>${weight}%</span></label>
  `).join("");
}

function renderMatrices() {
  matrix("impact-effort", "effort", "impact");
  matrix("strategy-readiness", "readiness", "strategic");
  matrix("evidence-urgency", "confidence", "urgency");
  matrix("leverage-difficulty", "effort", "leverage");
  const table = document.querySelector("[data-priority-table]");
  if (table) {
    const ranked = sortProblems(priorityState.problems.filter((p) => p.status !== "archived"), "score");
    table.innerHTML = `<thead><tr><th>Rank</th><th>Problem</th><th>Score</th><th>Spectrum</th><th>Cynefin</th><th>Archetypes</th></tr></thead><tbody>${ranked.map((problem, index) => `<tr><td>${index + 1}</td><td>${escapeHtml(problem.title)}</td><td>${problem.overall}</td><td>${titleCase(problem.spectrum)}</td><td>${titleCase(problem.cynefin)}</td><td>${problem.archetypes.map(titleCase).join(", ")}</td></tr>`).join("")}</tbody>`;
  }
}

function matrix(name, xKey, yKey) {
  const target = document.querySelector(`[data-matrix="${name}"]`);
  if (!target) return;
  target.innerHTML = `<span class="axis x">Higher ${titleCase(xKey)} →</span><span class="axis y">Higher ${titleCase(yKey)} ↑</span>` + priorityState.problems.filter((p) => p.status !== "archived").map((problem) => {
    const x = ((problem.scores[xKey] || 3) - 1) * 24 + 3;
    const y = 100 - (((problem.scores[yKey] || 3) - 1) * 24 + 8);
    return `<button class="matrix-node ${problem.spectrum}" style="left:${x}%;top:${y}%" title="${escapeAttr(problem.title)}" data-focus-problem="${problem.id}">${problem.overall}</button>`;
  }).join("");
}

function renderHeatmaps() {
  heatmap("[data-business-heatmap]", ["strategy", "governance", "finance", "operations", "data", "innovation", "regulation", "resilience"]);
  heatmap("[data-human-heatmap]", ["leadership", "behaviour", "incentives", "skills", "participation", "wellbeing", "justice", "customer experience"]);
  heatmap("[data-planetary-heatmap]", ["climate", "energy", "water", "materials", "waste", "biodiversity", "land", "ecosystem dependence"]);
  heatmap("[data-evidence-heatmap]", ["high confidence", "partial evidence", "low confidence", "assumption only", "missing data", "needs research"]);
}

function heatmap(selector, rows) {
  const target = document.querySelector(selector);
  if (!target) return;
  target.innerHTML = rows.map((row) => {
    const count = priorityState.problems.filter((p) => `${p.title} ${p.description} ${p.cluster}`.toLowerCase().includes(row.split(" ")[0])).length;
    return `<span class="${count > 2 ? "high" : count ? "medium" : "low"}">${row}<b>${count}</b></span>`;
  }).join("");
}

function renderRecommendations() {
  const groups = {
    "Low-hanging fruit": priorityState.problems.filter((p) => p.archetypes.includes("quick-win")),
    "Strategic priorities": priorityState.problems.filter((p) => p.archetypes.includes("strategic-programme")),
    "System leverage opportunities": priorityState.problems.filter((p) => p.archetypes.includes("system-leverage-point")),
    "Research or experiment first": priorityState.problems.filter((p) => p.archetypes.includes("research-needed") || p.archetypes.includes("experiment-first")),
    "Build capability": priorityState.problems.filter((p) => p.archetypes.includes("build-capability")),
    "Pause or monitor": priorityState.problems.filter((p) => p.archetypes.includes("pause-monitor"))
  };
  setHtml("[data-recommendation-groups]", Object.entries(groups).map(([group, items]) => `
    <section class="recommendation-group">
      <h3>${group}</h3>
      ${items.length ? items.slice(0, 4).map((problem, index) => recommendationCard(problem, index + 1)).join("") : "<p>No problems currently assigned.</p>"}
    </section>
  `).join(""));
}

function recommendationCard(problem, rank) {
  const trace = problem.evidenceTrace || {};
  const scoreTrace = problem.scoreTrace || {};
  const missing = Array.isArray(trace.missingPerspectives) && trace.missingPerspectives.length ? trace.missingPerspectives.join(", ") : "none";
  const drivers = Array.isArray(scoreTrace.topPositiveFactors) && scoreTrace.topPositiveFactors.length ? scoreTrace.topPositiveFactors.join(", ") : "score balance";
  return `
    <article class="recommendation-card" data-problem="${problem.id}">
      <span class="confidence-badge">Rank ${rank} · score ${problem.overall}</span>
      <h4>${escapeHtml(problem.title)}</h4>
      <p>${classificationRationale(problem, "cynefin")} Recommended next move: ${nextMove(problem)}.</p>
      <details>
        <summary>Why this recommendation?</summary>
        <p>Main score drivers: ${escapeHtml(drivers)}.</p>
        <p>Missing perspective evidence: ${escapeHtml(missing)}.</p>
        <p>${escapeHtml(problem.evidence || "Evidence summary needs review.")}</p>
      </details>
      <button type="button" data-select-problem>${priorityState.selectedIds.includes(problem.id) ? "Remove from focus" : "Add to shortlist"}</button>
    </article>
  `;
}

function renderSelection() {
  const selected = priorityState.problems.filter((p) => priorityState.selectedIds.includes(p.id));
  setHtml("[data-selection-panel]", `
    <div class="selected-counter"><strong>${selected.length} selected</strong><span>Recommended 3–5 · maximum 5</span></div>
    <div class="problem-card-list">${priorityState.problems.filter((p) => p.status !== "archived").map((problem) => `
      <article class="selection-card ${priorityState.selectedIds.includes(problem.id) ? "selected" : ""}" data-problem="${problem.id}">
        <h3>${escapeHtml(problem.title)}</h3>
        <p>${problem.overall} score · ${titleCase(problem.spectrum)} · ${titleCase(problem.cynefin)}</p>
        <button type="button" data-select-problem>${priorityState.selectedIds.includes(problem.id) ? "Selected" : "Select"}</button>
      </article>
    `).join("")}</div>
  `);
  const warnings = portfolioWarnings(selected);
  setHtml("[data-portfolio-warnings]", warnings.length ? warnings.map((warning) => `<p class="inline-insight">${warning}</p>`).join("") : `<p class="inline-insight">The current portfolio has no major balance warnings.</p>`);
}

function renderPathways() {
  const selected = priorityState.problems.filter((p) => priorityState.selectedIds.includes(p.id));
  setHtml("[data-decision-pathways]", selected.length ? selected.map((problem) => `
    <details class="pathway-card">
      <summary><b>${escapeHtml(problem.title)}</b><small>${titleCase(problem.cynefin)} · ${nextMove(problem)}</small></summary>
      <ol>
        <li><strong>Problem clarity:</strong> ${qualityFlags(problem).join(", ")}</li>
        <li><strong>Evidence:</strong> ${problem.confidence}/5 confidence; ${problem.evidence || "source missing"}</li>
        <li><strong>Complexity:</strong> ${titleCase(problem.cynefin)} response style</li>
        <li><strong>Influence:</strong> ${problem.scores.influence}/5</li>
        <li><strong>Capability:</strong> readiness ${problem.scores.readiness}/5</li>
        <li><strong>Response type:</strong> ${nextMove(problem)}</li>
        <li><strong>Data required:</strong> ${problem.confidence <= 2 ? "additional evidence and source verification" : "confirm existing evidence"}</li>
        <li><strong>Next-page route:</strong> ${nextMove(problem)}</li>
      </ol>
    </details>
  `).join("") : "<p>Select at least one priority problem to generate pathways.</p>");
  setHtml("[data-tool-routing]", selected.length ? selected.map((problem) => `
    <article class="tool-route-card">
      <h3>${escapeHtml(problem.title)}</h3>
      <p>${toolRouting(problem).join("; ")}.</p>
      <a href="../resources/">View related resources</a>
    </article>
  `).join("") : "");
}

function renderDashboard() {
  const selected = priorityState.problems.filter((p) => priorityState.selectedIds.includes(p.id));
  const dashboard = document.querySelector("[data-portfolio-dashboard]");
  if (dashboard) {
    const metrics = [
      ["Problems imported", priorityState.problems.length],
      ["Duplicates suggested", duplicatePairs().length],
      ["Problems classified", priorityState.problems.filter((p) => p.spectrum && p.cynefin).length],
      ["Recommended priorities", sortProblems(priorityState.problems, "score").slice(0, 5).length],
      ["Problems selected", selected.length],
      ["Research gaps", priorityState.problems.filter((p) => p.archetypes.includes("research-needed")).length],
      ["Quick wins", priorityState.problems.filter((p) => p.archetypes.includes("quick-win")).length],
      ["Strategic programmes", priorityState.problems.filter((p) => p.archetypes.includes("strategic-programme")).length]
    ];
    dashboard.innerHTML = metrics.map(([label, value]) => `<article class="metric-card"><strong>${value}</strong><span>${label}</span></article>`).join("");
  }
  setHtml("[data-selected-summary]", selected.length ? selected.map((problem) => `
    <article class="summary-priority">
      <h3>${escapeHtml(problem.title)}</h3>
      <p>Selected because it has a decision-support score of ${problem.overall}, ${titleCase(problem.spectrum)} ambition and ${titleCase(problem.cynefin)} complexity. Next route: ${nextMove(problem)}.</p>
    </article>
  `).join("") : "<p>No priorities selected yet.</p>");
  const panel = document.querySelector("[data-portfolio-panel]");
  if (panel) {
    panel.innerHTML = [
      ["Total problem count", priorityState.problems.length],
      ["Confirmed problems", priorityState.problems.filter((p) => p.status === "confirmed").length],
      ["Low-confidence problems", priorityState.problems.filter((p) => p.confidence <= 2).length],
      ["Quick wins", priorityState.problems.filter((p) => p.archetypes.includes("quick-win")).length],
      ["Strategic priorities", priorityState.problems.filter((p) => p.archetypes.includes("strategic-programme")).length],
      ["Selected problems", selected.length],
      ["Portfolio balance", portfolioWarnings(selected).length ? "Needs review" : "Balanced enough"]
    ].map(([label, value]) => `<div class="summary-row"><dt>${label}</dt><dd>${value}</dd></div>`).join("");
  }
  setText("[data-portfolio-insight]", latestPortfolioInsight(selected));
}

function updatePriorityProgress() {
  const selected = priorityState.selectedIds.length;
  const complete = [
    priorityState.problems.length > 0,
    duplicatePairs().length === 0 || priorityState.problems.some((p) => p.status === "confirmed"),
    priorityState.problems.every((p) => p.spectrum),
    priorityState.problems.every((p) => p.cynefin),
    Object.keys(priorityState.weights).length > 0,
    selected >= 1 && selected <= 5,
    selected >= 1,
    document.querySelector('[name="priorityReviewed"]')?.checked
  ].filter(Boolean).length;
  setText("[data-priority-progress-label]", `Sort and Prioritise · ${complete} of 8 sections complete`);
  setText("[data-priority-progress-detail]", `${priorityState.problems.length} problem signals reviewed · ${selected} selected`);
  setText("[data-priority-time]", `Approximately ${Math.max(4, 25 - complete * 3)} minutes remaining`);
  const fill = document.querySelector("[data-priority-progress-fill]");
  if (fill) fill.style.width = `${Math.round((complete / 8) * 100)}%`;
  document.querySelectorAll("[data-priority-section]").forEach((section) => {
    const state = section.querySelector("[data-priority-state]");
    if (state) state.textContent = section.open ? "In progress" : complete ? "Review" : "Not started";
  });
}

function suggestSpectrum(text) {
  if (text.includes("regenerative") || text.includes("ecosystem") || text.includes("nature")) return "dark";
  if (text.includes("redesign") || text.includes("supplier") || text.includes("traceability") || text.includes("culture")) return "mid";
  if (text.includes("report") || text.includes("data") || text.includes("waste") || text.includes("energy")) return "light";
  return "white";
}

function suggestCynefin(text, problem) {
  if (text.includes("crisis") || text.includes("disruption")) return "chaotic";
  if (text.includes("culture") || text.includes("behaviour") || text.includes("stakeholder") || text.includes("supplier")) return "complex";
  if (text.includes("material") || text.includes("product") || text.includes("analysis")) return "complicated";
  if (problem.confidence <= 2) return "confused";
  return "clear";
}

function suggestScores(text, problem) {
  return {
    impact: text.includes("supplier") || text.includes("climate") || text.includes("waste") ? 4 : 3,
    effort: text.includes("system") || text.includes("supplier") || text.includes("culture") ? 4 : 2,
    strategic: text.includes("strategy") || text.includes("supplier") || text.includes("governance") ? 5 : 3,
    urgency: text.includes("regulation") || text.includes("risk") || text.includes("incomplete") ? 4 : 3,
    confidence: problem.confidence || 3,
    readiness: text.includes("capability") || text.includes("ownership") ? 2 : 3,
    influence: text.includes("external") || text.includes("supplier") ? 3 : 4,
    leverage: text.includes("data") || text.includes("governance") || text.includes("supplier") ? 5 : 3,
    stakeholder: text.includes("employee") || text.includes("community") || text.includes("customer") ? 4 : 3,
    learning: text.includes("uncertain") || text.includes("culture") || text.includes("experiment") ? 5 : 3,
    regenerative: text.includes("nature") || text.includes("regenerative") ? 5 : 2
  };
}

function calculateScore(problem) {
  const s = problem.scores || {};
  const w = priorityState.weights;
  const positive = (s.impact || 3) * w.impact + (s.strategic || 3) * w.strategic + (s.leverage || 3) * w.leverage + (s.urgency || 3) * w.urgency + (s.influence || 3) * w.influence + (s.readiness || 3) * w.readiness + (s.confidence || 3) * w.confidence + (s.stakeholder || 3) * w.stakeholder + (s.learning || 3) * w.learning;
  const penalty = (s.effort || 3) * w.effort;
  return Math.max(0, Math.round((positive - penalty) / 5));
}

function assignArchetypes(problem) {
  const s = problem.scores;
  const types = [];
  if (s.impact >= 4 && s.effort <= 2 && s.confidence >= 3 && s.readiness >= 3) types.push("quick-win");
  if (s.impact >= 4 && s.strategic >= 4 && s.effort >= 3) types.push("strategic-programme");
  if (s.confidence <= 2) types.push("research-needed");
  if (problem.cynefin === "complex") types.push("experiment-first");
  if (s.strategic >= 4 && s.readiness <= 2) types.push("build-capability");
  if (s.leverage >= 4) types.push("system-leverage-point");
  if (["white", "light"].includes(problem.spectrum) && ["clear", "complicated"].includes(problem.cynefin)) types.push("compliance-foundation");
  if (["mid", "dark"].includes(problem.spectrum) && s.leverage >= 4) types.push("transformation-opportunity");
  if (problem.cynefin === "chaotic") types.push("crisis-response");
  if (s.urgency <= 2 && s.impact <= 2) types.push("pause-monitor");
  return types.length ? types : ["strategic-programme"];
}

function duplicatePairs() {
  const pairs = [];
  for (let i = 0; i < priorityState.problems.length; i++) {
    for (let j = i + 1; j < priorityState.problems.length; j++) {
      if (priorityState.problems[i].cluster === priorityState.problems[j].cluster) pairs.push([priorityState.problems[i], priorityState.problems[j]]);
    }
  }
  return pairs.slice(0, 4);
}

function qualityFlags(problem) {
  const flags = [];
  if (problem.description.length < 80) flags.push("Too narrow");
  if (!problem.description.includes("because")) flags.push("Underlying cause unclear");
  if (!problem.description.includes("leading to")) flags.push("Impact not explicit");
  if (problem.confidence <= 2) flags.push("Weak evidence");
  if (!flags.length) flags.push("Clear");
  return flags;
}

function confidenceNumber(value) {
  if (typeof value === "number") return value;
  if (value === "high") return 4;
  if (value === "medium") return 3;
  if (value === "low") return 2;
  if (value === "assumption") return 1;
  return 2;
}

function clusterFromText(text) {
  const lower = text.toLowerCase();
  if (lower.includes("supplier") || lower.includes("supply")) return "Operations and value chain";
  if (lower.includes("data") || lower.includes("evidence") || lower.includes("report")) return "Data and measurement";
  if (lower.includes("governance") || lower.includes("ownership")) return "Strategy and governance";
  if (lower.includes("employee") || lower.includes("culture") || lower.includes("behaviour")) return "People and culture";
  if (lower.includes("climate") || lower.includes("waste") || lower.includes("nature") || lower.includes("material")) return "Climate and nature";
  return "Strategy and governance";
}

function classificationRationale(problem, field) {
  if (field === "spectrum") return `Suggested as ${titleCase(problem.spectrum)} because the problem language and source context imply ${problem.spectrum === "white" ? "foundational capability" : problem.spectrum === "light" ? "harm reduction or compliance improvement" : problem.spectrum === "mid" ? "integrated organisational change" : problem.spectrum === "dark" ? "systemic or regenerative change" : "insufficient evidence"}.`;
  return `Suggested as ${titleCase(problem.cynefin)} because the problem appears to involve ${problem.cynefin === "complex" ? "interacting actors and uncertain outcomes" : problem.cynefin === "complicated" ? "expert analysis and several valid solutions" : problem.cynefin === "clear" ? "visible cause and effect" : problem.cynefin === "chaotic" ? "immediate instability" : "unclear or mixed evidence"}.`;
}

function nextMove(problem) {
  if (problem.cynefin === "complex") return "Design experiment";
  if (problem.cynefin === "confused" || problem.confidence <= 2) return "Gather evidence first";
  if (problem.scores.readiness <= 2) return "Build capability first";
  if (problem.cynefin === "chaotic") return "Stabilise immediately";
  return "Proceed to structured decision";
}

function toolRouting(problem) {
  if (problem.cynefin === "complex") return ["systems mapping", "stakeholder interviews", "safe-to-fail experiments", "assumptions mapping"];
  if (problem.cynefin === "complicated") return ["expert analysis", "LCA", "material comparison", "scenario planning"];
  if (problem.cynefin === "clear") return ["process mapping", "responsibility matrix", "data dictionary", "workflow standardisation"];
  if (problem.cynefin === "chaotic") return ["rapid risk control", "emergency governance", "short decision cycle"];
  return ["research plan", "evidence gap review", "problem reframing"];
}

function portfolioWarnings(selected) {
  const warnings = [];
  if (selected.length > 5) warnings.push("More than five problems are selected. Reduce the list to create focus.");
  if (selected.length && selected.every((p) => p.scores.effort >= 4)) warnings.push("All selected problems are high-effort.");
  if (selected.length && !selected.some((p) => `${p.cluster} ${p.title}`.toLowerCase().includes("people") || `${p.cluster} ${p.title}`.toLowerCase().includes("culture"))) warnings.push("No selected problem clearly addresses Human Empathy findings.");
  if (selected.filter((p) => p.confidence <= 2).length >= 3) warnings.push("Several selected problems depend on weak evidence.");
  if (selected.length && !selected.some((p) => p.archetypes.includes("quick-win"))) warnings.push("The portfolio contains no near-term quick win.");
  return warnings;
}

function latestPortfolioInsight(selected) {
  const lowData = priorityState.problems.filter((p) => p.cluster === "Data and measurement" && p.confidence <= 2).length;
  if (lowData >= 2) return "Several high-impact problems rely on weak or fragmented data. Consider treating data capability as a shared enabling priority.";
  if (selected.length > 5) return "The selected portfolio is too broad for focused action. Reduce to three to five problems.";
  if (selected.length >= 3) return "The selected portfolio is ready for decision-pathway preparation, subject to evidence and readiness checks.";
  return "Review recommendations and select a focused portfolio to generate decision pathways.";
}

function sortProblems(items, sort) {
  const copy = [...items];
  if (sort === "confidence-low") return copy.sort((a, b) => a.confidence - b.confidence);
  if (sort === "impact") return copy.sort((a, b) => b.scores.impact - a.scores.impact);
  if (sort === "newest") return copy.reverse();
  return copy.sort((a, b) => b.overall - a.overall);
}

function countBy(items, key) {
  return items.reduce((acc, item) => ({ ...acc, [item[key]]: (acc[item[key]] || 0) + 1 }), {});
}

function savePriority() {
  clearTimeout(savePriority.timer);
  const autosave = document.querySelector("[data-priority-autosave]");
  if (autosave) autosave.textContent = "Saving";
  savePriority.timer = setTimeout(() => {
    const snapshot = prioritySnapshot();
    localStorage.setItem(priorityKey, JSON.stringify(snapshot));
    if (!priorityBackendReady) {
      if (autosave) autosave.textContent = "Saved locally";
      return;
    }
    savePriorityBackend(snapshot).then((saved) => {
      if (saved?.stateId) {
        priorityState.stateId = saved.stateId;
        localStorage.setItem(priorityKey, JSON.stringify({ ...snapshot, stateId: saved.stateId }));
      }
      if (autosave) autosave.textContent = saved?.ok === false ? "Saved locally" : "Saved just now";
    });
  }, 220);
}

function activeJourneyId() {
  return onboardingPriority.journeyId || savedPriority.journeyId || impactData.journeyId || "anonymous-local";
}

function prioritySnapshot() {
  return {
    stateId: priorityState.stateId || "",
    sourceImpactJourneyStateId: priorityState.sourceImpactJourneyStateId || impactData.stateId || "",
    problems: priorityState.problems,
    weights: priorityState.weights,
    selectedIds: priorityState.selectedIds,
    reviewed: Boolean(document.querySelector('[name="priorityReviewed"]')?.checked || priorityState.reviewed),
    savedAt: new Date().toISOString()
  };
}

async function hydratePriorityFromBackend() {
  try {
    const response = await fetch(`/api/journeys/${encodeURIComponent(activeJourneyId())}/prioritisation?anonymousSessionId=${encodeURIComponent(priorityAnonymousSessionId)}`);
    if (!response.ok) throw new Error("Prioritisation backend unavailable");
    const data = await response.json();
    if (data.formData) {
      priorityState.stateId = data.stateId || data.formData.stateId || priorityState.stateId;
      priorityState.sourceImpactJourneyStateId = data.formData.sourceImpactJourneyStateId || data.page4?.sourceImpactJourneyStateId || priorityState.sourceImpactJourneyStateId;
      priorityState.problems = Array.isArray(data.formData.problems) && data.formData.problems.length ? data.formData.problems : priorityState.problems;
      priorityState.weights = data.formData.weights || priorityState.weights;
      priorityState.selectedIds = data.formData.selectedIds || priorityState.selectedIds;
      priorityState.reviewed = Boolean(data.formData.reviewed);
      const reviewed = document.querySelector('[name="priorityReviewed"]');
      if (reviewed) reviewed.checked = priorityState.reviewed;
      localStorage.setItem(priorityKey, JSON.stringify(prioritySnapshot()));
      priorityState.problems = priorityState.problems.map(enrichProblem);
      renderAll();
    }
    priorityBackendReady = true;
  } catch (error) {
    priorityBackendReady = true;
    console.warn("Prioritisation backend restore unavailable", error);
  }
}

async function savePriorityBackend(snapshot, status = "draft") {
  try {
    const endpoint = priorityState.stateId
      ? `/api/prioritisation/${encodeURIComponent(priorityState.stateId)}/${status === "completed" ? "complete" : "autosave"}`
      : `/api/journeys/${encodeURIComponent(activeJourneyId())}/prioritisation`;
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        anonymousSessionId: priorityAnonymousSessionId,
        journeyId: activeJourneyId(),
        priorityStateId: priorityState.stateId || undefined,
        status,
        formData: snapshot
      })
    });
    return response.ok ? response.json() : { ok: false };
  } catch (error) {
    console.warn("Prioritisation backend save unavailable", error);
    return { ok: false };
  }
}

function restoreReview() {
  document.querySelector('[name="priorityReviewed"]')?.addEventListener("change", renderAll);
}

document.addEventListener("input", (event) => {
  const problemCard = event.target.closest("[data-problem]");
  if (problemCard && event.target.dataset.problemField) {
    const problem = findProblem(problemCard.dataset.problem);
    problem[event.target.dataset.problemField] = event.target.textContent;
    problem.userEdited = true;
  }
  if (event.target.dataset.score) {
    const problem = findProblem(event.target.closest("[data-problem]").dataset.problem);
    problem.scores[event.target.dataset.score] = Number(event.target.value);
    event.target.nextElementSibling.textContent = event.target.value;
  }
  if (event.target.dataset.weight) {
    priorityState.weights[event.target.dataset.weight] = Number(event.target.value);
    event.target.nextElementSibling.textContent = `${event.target.value}%`;
  }
  renderAll();
});

document.addEventListener("change", (event) => {
  if (event.target.dataset.classification) {
    const problem = findProblem(event.target.closest("[data-problem]").dataset.problem);
    problem[event.target.dataset.classification] = event.target.value;
    problem.userEdited = true;
    renderAll();
  }
  if (event.target.matches("[data-problem-search], [data-problem-filter], [data-problem-sort]")) renderProblemList();
});

document.addEventListener("click", (event) => {
  const problemCard = event.target.closest("[data-problem]");
  if (problemCard && event.target.dataset.status) {
    findProblem(problemCard.dataset.problem).status = event.target.dataset.status;
    renderAll();
  }
  if (problemCard && event.target.matches("[data-select-problem]")) {
    const id = problemCard.dataset.problem;
    if (priorityState.selectedIds.includes(id)) priorityState.selectedIds = priorityState.selectedIds.filter((item) => item !== id);
    else if (priorityState.selectedIds.length < 5) priorityState.selectedIds.push(id);
    findProblem(id).status = priorityState.selectedIds.includes(id) ? "selected" : "confirmed";
    renderAll();
  }
  if (event.target.dataset.merge) {
    const [aId, bId] = event.target.dataset.merge.split("|");
    const a = findProblem(aId);
    const b = findProblem(bId);
    a.title = `${a.title} / ${b.title}`;
    a.description = `${a.description} ${b.description}`;
    a.evidence = `${a.evidence}; ${b.evidence}`;
    a.status = "confirmed";
    priorityState.problems = priorityState.problems.filter((p) => p.id !== bId);
    renderAll();
  }
  if (event.target.matches("[data-priority-next]")) {
    const current = event.target.closest(".onboarding-section");
    const next = current?.nextElementSibling;
    if (current) current.open = false;
    if (next?.matches(".onboarding-section")) {
      next.open = true;
      next.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    renderAll();
  }
  if (event.target.matches("[data-priority-resource-toggle]")) {
    const panel = document.querySelector("[data-priority-resource-panel]");
    if (panel) panel.hidden = !panel.hidden;
  }
  if (event.target.matches("[data-review-impact]")) {
    alert(`Impact Journey outputs found: ${(impactData.problemSignals || []).length} problem signals, ${(impactData.stages || []).length} stages and ${Object.keys(impactData.layerItems || {}).length} mapped stage records.`);
  }
  if (event.target.matches("[data-priority-download]")) {
    const blob = new Blob([JSON.stringify(priorityState, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `green-spectrum-priority-${event.target.dataset.priorityDownload}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }
  if (event.target.matches("[data-priority-save-exit]")) {
    savePriority();
    window.location.href = "../";
  }
  if (event.target.matches("[data-dismiss-priority-insight]")) {
    event.target.closest(".generated-insight").hidden = true;
  }
  if (event.target.matches("[data-priority-continue]")) {
    if (!document.querySelector('[name="priorityReviewed"]')?.checked) {
      event.preventDefault();
      document.querySelector('[name="priorityReviewed"]')?.focus();
      return;
    }
    event.preventDefault();
    const snapshot = prioritySnapshot();
    savePriorityBackend(snapshot, "completed").then((saved) => {
      if (saved?.ok) {
        window.location.href = event.target.href;
        return;
      }
      const autosave = document.querySelector("[data-priority-autosave]");
      if (autosave) autosave.textContent = "Review required";
      console.warn("Prioritisation completion blocked", saved);
    });
  }
});

function findProblem(id) {
  return priorityState.problems.find((problem) => problem.id === id);
}

function titleCase(value) {
  return String(value || "").replaceAll("-", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function setHtml(selector, html) {
  const target = document.querySelector(selector);
  if (target) target.innerHTML = html;
}

function setText(selector, value) {
  const target = document.querySelector(selector);
  if (target) target.textContent = value;
}

function escapeHtml(value) {
  return String(value || "").replace(/[&<>"']/g, (match) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#039;" }[match]));
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/"/g, "&quot;");
}
