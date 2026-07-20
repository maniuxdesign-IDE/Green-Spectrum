const prototypeKey = "greenSpectrum.prototype.v1";
const sessionKey = "greenSpectrum.sessionId.v1";
const prototypeAnonymousSessionId = localStorage.getItem(sessionKey) || `gs-${Date.now()}-${Math.random().toString(16).slice(2)}`;
localStorage.setItem(sessionKey, prototypeAnonymousSessionId);
const priorityData = JSON.parse(localStorage.getItem("greenSpectrum.priority.v1") || "{}");
const onboardingData = JSON.parse(localStorage.getItem("greenSpectrum.onboarding.v1") || "{}");
const savedPrototype = JSON.parse(localStorage.getItem(prototypeKey) || "{}");

const prototypeTypes = ["behaviour", "process", "service", "digital", "product", "policy", "supply-chain", "business-model", "community", "organisational", "regenerative"];
const interventionFamilies = ["behaviour", "process", "governance", "policy", "data", "technology", "product", "service", "supply-chain", "business-model", "capability", "collaboration", "regenerative"];
const metricCategories = ["input", "activity", "output", "outcome", "impact", "learning"];
const activePrototypeSections = ["review", "outcome", "interventions", "prototype", "ownership"];

const prototypeState = {
  stateId: savedPrototype.stateId || "",
  sourcePriorityStateId: savedPrototype.sourcePriorityStateId || "",
  sourcePriorityPortfolioId: savedPrototype.sourcePriorityPortfolioId || "",
  pathways: savedPrototype.pathways || importPathways(),
  activeId: savedPrototype.activeId || "",
  primaryIds: savedPrototype.primaryIds || [],
  reviewed: Boolean(savedPrototype.reviewed)
};
let prototypeBackendReady = false;

if (!prototypeState.activeId && prototypeState.pathways[0]) prototypeState.activeId = prototypeState.pathways[0].id;
if (!prototypeState.primaryIds.length) prototypeState.primaryIds = prototypeState.pathways.slice(0, 3).map((p) => p.id);

document.querySelector("[data-prototype-organisation]").textContent = onboardingData.organisationName || "New journey";
renderPrototypeAll();
hydratePrototypeFromBackend();

function importPathways() {
  const selected = (priorityData.problems || []).filter((problem) => (priorityData.selectedIds || []).includes(problem.id));
  const source = selected.length ? selected : (priorityData.problems || []).slice(0, 3);
  const fallback = source.length ? source : [
    { id: "demo-1", title: "Supplier emissions data pathway", description: "Supplier emissions data is incomplete because reporting expectations and verification processes are inconsistent, leading to weak Scope 3 confidence.", spectrum: "light", cynefin: "complex", scores: { impact: 4, effort: 3, strategic: 5, urgency: 4, readiness: 3, influence: 3, leverage: 5 }, archetypes: ["experiment-first", "system-leverage-point"], evidence: "Prototype placeholder" },
    { id: "demo-2", title: "Packaging waste reduction pathway", description: "Packaging waste remains high because product design and end-of-life ownership are disconnected, leading to avoidable material loss.", spectrum: "mid", cynefin: "complicated", scores: { impact: 4, effort: 3, strategic: 4, urgency: 3, readiness: 3, influence: 4, leverage: 4 }, archetypes: ["strategic-programme"], evidence: "Prototype placeholder" },
    { id: "demo-3", title: "Sustainability governance pathway", description: "Sustainability governance exists but accountability is not linked to operational decision points, leading to inconsistent delivery.", spectrum: "light", cynefin: "clear", scores: { impact: 3, effort: 2, strategic: 4, urgency: 3, readiness: 4, influence: 4, leverage: 5 }, archetypes: ["quick-win"], evidence: "Prototype placeholder" }
  ];
  return fallback.slice(0, 5).map((problem, index) => createPathway(problem, index));
}

function createPathway(problem, index) {
  const route = nextRoute(problem);
  const family = recommendedFamily(problem);
  return {
    id: `pathway-${problem.id || index}`,
    problemId: problem.id,
    rank: index + 1,
    title: problem.title || `Pathway ${index + 1}`,
    problemDefinition: problem.description || problem.title || "",
    evidenceSummary: problem.evidence || "Source evidence carried forward from prioritisation.",
    unknowns: problem.confidence <= 2 ? ["Evidence confidence remains low"] : [],
    spectrum: problem.spectrum || "light",
    cynefin: problem.cynefin || "complex",
    archetypes: problem.archetypes || [],
    readiness: problem.scores?.readiness || 3,
    influence: problem.scores?.influence || 3,
    leverage: problem.scores?.leverage || 3,
    desiredOutcome: "",
    beneficiaries: [],
    changes: [],
    nonNegotiables: "",
    timeframe: "3–12 months",
    backcastSteps: ["Define evidence need", "Confirm owner", "Test the riskiest assumption", "Review decision threshold"],
    decisionAnswers: {},
    decisionOutcome: route,
    decisionRationale: decisionRationale(route, problem),
    interventionOptions: generateInterventions(problem, family),
    selectedInterventionId: "",
    horizons: defaultHorizons(problem),
    prototypeType: recommendedPrototype(problem, family),
    experiment: defaultExperiment(problem, family),
    owners: { executiveSponsor: "", pathwayOwner: "", experimentOwner: "", decisionMaker: "", dataOwner: "", riskOwner: "", cadence: "monthly" },
    metrics: defaultMetrics(problem),
    risks: defaultRisks(problem),
    reviewDate: "",
    completed: false
  };
}

function renderPrototypeAll() {
  renderPathwayCards();
  renderSelector();
  renderActiveSections();
  renderPortfolio();
  renderPanel();
  renderCompletion();
  updatePrototypeProgress();
  savePrototype();
}

function activePathway() {
  return prototypeState.pathways.find((p) => p.id === prototypeState.activeId) || prototypeState.pathways[0];
}

function renderPathwayCards() {
  const target = document.querySelector("[data-selected-pathway-cards]");
  if (!target) return;
  target.innerHTML = prototypeState.pathways.map((p) => `
    <article class="pathway-orientation-card ${prototypeState.primaryIds.includes(p.id) ? "primary" : ""}" data-pathway-card="${p.id}">
      <span class="confidence-badge">Priority ${p.rank} · ${titleCase(p.spectrum)} · ${titleCase(p.cynefin)}</span>
      <h3>${escapeHtml(p.title)}</h3>
      <p>${escapeHtml(p.problemDefinition)}</p>
      <dl><div><dt>Prototype route</dt><dd>${titleCase(p.prototypeType)}</dd></div><div><dt>Readiness</dt><dd>${p.readiness}/5</dd></div><div><dt>Leverage</dt><dd>${p.leverage}/5</dd></div></dl>
      <div class="problem-actions">
        <button type="button" data-open-pathway="${p.id}">Open pathway</button>
        <button type="button" data-toggle-primary="${p.id}">${prototypeState.primaryIds.includes(p.id) ? "Primary" : "Mark primary"}</button>
        <a href="../sort-prioritise/">Review priority</a>
      </div>
    </article>
  `).join("");
}

function renderSelector() {
  const target = document.querySelector("[data-pathway-selector]");
  if (!target) return;
  target.innerHTML = prototypeState.pathways.map((p, index) => `<button type="button" class="${p.id === prototypeState.activeId ? "active" : ""}" data-open-pathway="${p.id}">Pathway ${index + 1}<small>${escapeHtml(p.title)}</small></button>`).join("");
}

function renderActiveSections() {
  const p = activePathway();
  if (!p) return;
  setHtml('[data-section-body="review"]', reviewMarkup(p));
  setHtml('[data-section-body="outcome"]', outcomeMarkup(p));
  setHtml('[data-section-body="backcast"]', backcastMarkup(p));
  setHtml('[data-section-body="decision"]', decisionMarkup(p));
  setHtml('[data-section-body="interventions"]', interventionsMarkup(p));
  setHtml('[data-section-body="horizons"]', horizonsMarkup(p));
  setHtml('[data-section-body="prototype"]', prototypeMarkup(p));
  setHtml('[data-section-body="ownership"]', ownershipMarkup(p));
  setHtml('[data-section-body="summary"]', summaryMarkup(p));
}

function reviewMarkup(p) {
  return `
    <article class="priority-problem-card">
      <span class="confidence-badge">Imported from prioritisation · ${titleCase(p.spectrum)} · ${titleCase(p.cynefin)}</span>
      <h3>${escapeHtml(p.title)}</h3>
      <p>${escapeHtml(p.problemDefinition)}</p>
      <dl><div><dt>Evidence</dt><dd>${escapeHtml(p.evidenceSummary)}</dd></div><div><dt>Readiness</dt><dd>${p.readiness}/5</dd></div><div><dt>Influence</dt><dd>${p.influence}/5</dd></div><div><dt>Leverage</dt><dd>${p.leverage}/5</dd></div></dl>
    </article>
    <fieldset><legend>Is the problem understood well enough?</legend><div class="selection-grid three">
      ${["Yes", "Mostly", "No", "Mixed problem"].map(v => radioCard("problemClear", v, p.decisionAnswers.problemClear)).join("")}
    </div></fieldset>
    <div class="form-grid">
      <label class="field-label">Problem type <select data-path-field="problemType"><option>root cause</option><option>symptom</option><option>combination</option><option>uncertain</option></select></label>
      <label class="field-label">System boundary <select data-path-field="boundary"><option>Yes</option><option>Too broad</option><option>Too narrow</option><option>Needs adjustment</option></select></label>
      <label class="field-label">Evidence status <select data-path-field="evidenceDecision"><option>Enough to experiment</option><option>Yes</option><option>More evidence required</option><option>Immediate action required despite uncertainty</option></select></label>
      <label class="field-label">Stakeholder agreement <select data-path-field="stakeholderAgreement"><option>Not yet tested</option><option>Strong agreement</option><option>Partial agreement</option><option>Significant disagreement</option></select></label>
      <label class="field-label full">What would change the problem definition? <textarea rows="3" data-path-field="definitionChange">${escapeHtml(p.definitionChange || "")}</textarea></label>
    </div>
    <p class="inline-insight">System decision: ${titleCase(p.decisionOutcome)}. ${p.decisionRationale}</p>
    <button class="button button-primary" type="button" data-prototype-next>Save and continue</button>
  `;
}

function outcomeMarkup(p) {
  return `
    <label class="field-label">Prototype aim <textarea rows="3" data-path-field="desiredOutcome" placeholder="What would this small test help you learn?">${escapeHtml(p.desiredOutcome)}</textarea></label>
    <fieldset><legend>Who benefits?</legend><div class="chip-grid large">${["employees", "customers", "suppliers", "communities", "investors", "ecosystems", "future generations"].map(v => checkChip("beneficiaries", v, p.beneficiaries)).join("")}</div></fieldset>
    <fieldset><legend>What changes?</legend><div class="chip-grid large">${["behaviour", "process", "policy", "governance", "data", "technology", "product", "service", "supply chain", "business model", "ecosystem", "capability", "culture"].map(v => checkChip("changes", v, p.changes)).join("")}</div></fieldset>
    <div class="form-grid">
      <label class="field-label">Prototype timeframe <select data-path-field="timeframe"><option ${p.timeframe === "0–3 months" ? "selected" : ""}>0–3 months</option><option ${p.timeframe === "3–12 months" ? "selected" : ""}>3–12 months</option><option ${p.timeframe === "12–36 months" ? "selected" : ""}>12–36 months</option><option ${p.timeframe === "3+ years" ? "selected" : ""}>3+ years</option><option ${p.timeframe === "Multiple horizons" ? "selected" : ""}>Multiple horizons</option></select></label>
      <label class="field-label">What should not be compromised? <input data-path-field="nonNegotiables" value="${escapeAttr(p.nonNegotiables || "")}" placeholder="Safety, quality, affordability, wellbeing"></label>
      <label class="field-label full">What does good enough to proceed look like? <textarea rows="3" data-path-field="goodEnough">${escapeHtml(p.goodEnough || "")}</textarea></label>
    </div>
    <p class="inline-insight">${outcomeQuality(p).join(", ")}</p>
    <button class="button button-primary" type="button" data-prototype-next>Save and continue</button>
  `;
}

function backcastMarkup(p) {
  return `
    <div class="backcast-flow">
      <article><span>Future state</span><p>${escapeHtml(p.desiredOutcome || "Define the desired outcome first.")}</p></article>
      ${p.backcastSteps.map((step, index) => `<article data-backcast="${index}"><span>Before that</span><input value="${escapeAttr(step)}" data-backcast-field></article>`).join("")}
      <article><span>Starting point</span><p>What can be done now?</p></article>
    </div>
    <div class="hero-actions"><button class="button button-secondary" type="button" data-add-backcast>Add step</button><button class="button button-primary" type="button" data-prototype-next>Save and continue</button></div>
  `;
}

function decisionMarkup(p) {
  const questions = [
    ["clarity", "Is the problem clearly understood?", ["yes", "no", "mixed"]],
    ["alignment", "Does the desired outcome align with strategy?", ["yes", "partial", "no"]],
    ["influence", "Can the organisation influence the problem?", ["direct control", "shared control", "requires partnership", "very limited"]],
    ["capability", "Does the organisation have the capability?", ["yes", "partial", "no"]],
    ["risk", "Is the level of risk acceptable?", ["yes", "redesign", "no"]],
    ["testable", "Can the intervention be tested?", ["yes", "partly", "no"]]
  ];
  return `
    <div class="decision-tree-list">
      ${questions.map(([key, label, values], index) => `<fieldset class="decision-question"><legend>${index + 1}. ${label}</legend><div class="selection-grid three">${values.map(v => radioCard(`decision-${key}`, v, p.decisionAnswers[key])).join("")}</div></fieldset>`).join("")}
    </div>
    <label class="field-label">Confirmed decision outcome <select data-path-field="decisionOutcome">${["proceed", "experiment", "pause", "archive", "return-to-discovery", "build-capability", "collaborate", "stabilise"].map(v => `<option value="${v}" ${p.decisionOutcome === v ? "selected" : ""}>${titleCase(v)}</option>`).join("")}</select></label>
    <label class="field-label">Decision rationale <textarea rows="3" data-path-field="decisionRationale">${escapeHtml(p.decisionRationale || "")}</textarea></label>
    <p class="inline-insight">Changing the decision outcome updates prototype and learning requirements.</p>
    <button class="button button-primary" type="button" data-prototype-next>Save and continue</button>
  `;
}

function interventionsMarkup(p) {
  return `
    <div class="intervention-options">${p.interventionOptions.map(option => `
      <article class="intervention-card ${p.selectedInterventionId === option.id ? "selected" : ""}" data-option="${option.id}">
        <span class="confidence-badge">${titleCase(option.family)} · ${option.status}</span>
        <h3>${escapeHtml(option.title)}</h3>
        <p>${escapeHtml(option.description)}</p>
        <dl><div><dt>Mechanism</dt><dd>${escapeHtml(option.mechanism)}</dd></div><div><dt>Impact</dt><dd>${option.impact}/5</dd></div><div><dt>Effort</dt><dd>${option.effort}/5</dd></div><div><dt>Risk</dt><dd>${option.risk}/5</dd></div></dl>
        <div class="problem-actions"><button type="button" data-select-option="${option.id}">${p.selectedInterventionId === option.id ? "Selected" : "Select primary intervention"}</button><button type="button" data-reject-option="${option.id}">Reject</button></div>
      </article>`).join("")}</div>
    <button class="button button-secondary" type="button" data-add-intervention>Add alternative</button>
    <button class="button button-primary" type="button" data-prototype-next>Save and continue</button>
  `;
}

function horizonsMarkup(p) {
  return `<div class="horizon-flow">${p.horizons.map(h => `
    <article class="horizon-card ${h.type}">
      <span class="confidence-badge">${h.title} · ${h.timeframe}</span>
      <label>Objective <textarea rows="2" data-horizon="${h.type}" data-horizon-field="objective">${escapeHtml(h.objective)}</textarea></label>
      <label>Actions <textarea rows="3" data-horizon="${h.type}" data-horizon-field="actions">${escapeHtml(h.actions.join("; "))}</textarea></label>
      <label>Owner <input data-horizon="${h.type}" data-horizon-field="owner" value="${escapeAttr(h.owner || "")}"></label>
      <label>Decision date <input type="date" data-horizon="${h.type}" data-horizon-field="decisionDate" value="${escapeAttr(h.decisionDate || "")}"></label>
    </article>`).join("")}</div><button class="button button-primary" type="button" data-prototype-next>Save and continue</button>`;
}

function prototypeMarkup(p) {
  return `
    <fieldset><legend>What is the smallest useful way to test this intervention?</legend><div class="selection-grid">${prototypeTypes.map(type => radioCard("prototypeType", type, p.prototypeType)).join("")}</div></fieldset>
    <div class="experiment-card-builder">
      <label class="field-label">Experiment title <textarea rows="2" data-experiment-field="title">${escapeHtml(p.experiment.title)}</textarea></label>
      <label class="field-label full">Initial hypothesis <textarea rows="4" data-experiment-field="hypothesis">${escapeHtml(p.experiment.hypothesis)}</textarea></label>
      <label class="field-label full">Learning objective <textarea rows="3" data-experiment-field="learningObjective">${escapeHtml(p.experiment.learningObjective)}</textarea></label>
      <label class="field-label full">Method <textarea rows="3" data-experiment-field="method">${escapeHtml(p.experiment.method)}</textarea></label>
      <div class="form-grid"><label class="field-label">Start date <input type="date" data-experiment-field="startDate" value="${escapeAttr(p.experiment.startDate || "")}"></label><label class="field-label">End date <input type="date" data-experiment-field="endDate" value="${escapeAttr(p.experiment.endDate || "")}"></label><label class="field-label full">Decision threshold <textarea rows="3" data-experiment-field="decisionThreshold">${escapeHtml(p.experiment.decisionThreshold || "")}</textarea></label></div>
    </div>
    <button class="button button-primary" type="button" data-prototype-next>Save and continue</button>
  `;
}

function ownershipMarkup(p) {
  return `
    <div class="form-grid">
      ${["experimentOwner", "decisionMaker", "dataOwner"].map(key => `<label class="field-label">${titleCase(key)} <input data-owner-field="${key}" value="${escapeAttr(p.owners[key] || "")}"></label>`).join("")}
      <label class="field-label">Review rhythm <select data-owner-field="cadence">${["weekly", "fortnightly", "monthly", "milestone-based", "custom"].map(v => `<option ${p.owners.cadence === v ? "selected" : ""}>${v}</option>`).join("")}</select></label>
      <label class="field-label">Review date <input type="date" data-path-field="reviewDate" value="${escapeAttr(p.reviewDate || "")}"></label>
    </div>
    <h3>One learning measure</h3>
    <div class="metric-list">${p.metrics.slice(0, 1).map((m, index) => metricMarkup(m, index)).join("")}</div>
    <h3>One risk to watch</h3>
    <div class="risk-list">${p.risks.slice(0, 1).map((r, index) => riskMarkup(r, index)).join("")}</div>
    <div class="prototype-placeholder-list" aria-label="Later placeholders">
      <span>Full KPI plan placeholder</span>
      <span>Risk register placeholder</span>
      <span>Governance workflow placeholder</span>
    </div>
    <button class="button button-primary" type="button" data-prototype-next>Save prototype card</button>
  `;
}

function summaryMarkup(p) {
  const selectedOption = p.interventionOptions.find(o => o.id === p.selectedInterventionId) || p.interventionOptions[0];
  return `
    <div class="strategic-pathway">
      ${["Problem", "Desired Outcome", "Decision", "Intervention", "Horizon 1", "Horizon 2", "Horizon 3", "Experiment", "Review", "Learn"].map((label, index) => `<article><span>${index + 1}</span><h3>${label}</h3><p>${summaryValue(p, label, selectedOption)}</p></article>`).join("")}
    </div>
    <fieldset><legend>Final pathway status</legend><div class="chip-grid large">${["draft", "ready", "active", "review"].map(v => radioPill("status", v, p.status || "draft")).join("")}</div></fieldset>
    <button class="button button-primary" type="button" data-confirm-pathway>Confirm pathway</button>
  `;
}

function metricMarkup(m, index) {
  return `<article class="metric-edit" data-metric="${index}"><label>Metric name <textarea rows="2" data-metric-field="name">${escapeHtml(m.name)}</textarea></label><label>Category <select data-metric-field="category">${metricCategories.map(c => `<option ${m.category === c ? "selected" : ""}>${c}</option>`).join("")}</select></label><label>Target <textarea rows="2" data-metric-field="target">${escapeHtml(m.target || "")}</textarea></label><label>Owner <input data-metric-field="owner" value="${escapeAttr(m.owner || "")}"></label></article>`;
}

function riskMarkup(r, index) {
  return `<article class="metric-edit" data-risk="${index}"><label>Risk <textarea rows="2" data-risk-field="description">${escapeHtml(r.description)}</textarea></label><label>Likelihood <select data-risk-field="likelihood">${[1,2,3,4,5].map(v => `<option ${r.likelihood == v ? "selected" : ""}>${v}</option>`).join("")}</select></label><label>Severity <select data-risk-field="severity">${[1,2,3,4,5].map(v => `<option ${r.severity == v ? "selected" : ""}>${v}</option>`).join("")}</select></label><label>Mitigation <textarea rows="2" data-risk-field="mitigation">${escapeHtml(r.mitigation || "")}</textarea></label></article>`;
}

function renderPortfolio() {
  const target = document.querySelector("[data-pathway-portfolio]");
  if (!target) return;
  target.innerHTML = prototypeState.pathways.map(p => {
    const selectedOption = p.interventionOptions.find(o => o.id === p.selectedInterventionId) || p.interventionOptions[0];
    return `<article class="portfolio-pathway-card ${p.completed ? "complete" : ""}">
      <span class="confidence-badge">${prototypeState.primaryIds.includes(p.id) ? "Prototype focus" : "Later"} · ${p.completed ? "ready" : "draft"}</span>
      <h3>${escapeHtml(p.title)}</h3>
      <p>${escapeHtml(p.desiredOutcome || "Outcome not defined yet.")}</p>
      <dl><div><dt>Intervention</dt><dd>${escapeHtml(selectedOption?.title || "Not selected")}</dd></div><div><dt>Prototype</dt><dd>${titleCase(p.prototypeType)}</dd></div><div><dt>Owner</dt><dd>${escapeHtml(p.owners.experimentOwner || p.owners.pathwayOwner || "Missing")}</dd></div><div><dt>Measure</dt><dd>${escapeHtml(p.metrics[0]?.name || "Missing")}</dd></div><div><dt>Review</dt><dd>${p.reviewDate || "Missing"}</dd></div></dl>
    </article>`;
  }).join("");
  const warnings = portfolioWarnings();
  setHtml("[data-prototype-warnings]", warnings.length ? warnings.map(w => `<p class="inline-insight">${w}</p>`).join("") : `<p class="inline-insight">The prototype card is ready enough for MVP testing once the owner, measure and review date are clear.</p>`);
}

function renderPanel() {
  const p = activePathway();
  if (!p) return;
  const selectedOption = p.interventionOptions.find(o => o.id === p.selectedInterventionId) || p.interventionOptions[0];
  setHtml("[data-prototype-panel]", [
    ["Active pathway", p.title],
    ["Prototype aim", p.desiredOutcome || "Missing"],
    ["Selected intervention", selectedOption?.title || "Not selected"],
    ["Prototype type", titleCase(p.prototypeType)],
    ["Experiment status", p.experiment.status || "draft"],
    ["Owner", p.owners.experimentOwner || p.owners.pathwayOwner || "Missing"],
    ["Next review date", p.reviewDate || "Missing"],
    ["Unresolved assumptions", p.unknowns.length]
  ].map(([label, value]) => `<div class="summary-row"><dt>${label}</dt><dd>${escapeHtml(value)}</dd></div>`).join(""));
  setText("[data-prototype-insight]", `${p.title} needs a clear prototype owner, learning measure and review date before user testing.`);
}

function renderCompletion() {
  const completed = prototypeState.pathways.filter(p => p.completed).length;
  const experiments = prototypeState.pathways.filter(p => p.experiment.title && p.experiment.hypothesis).length;
  setHtml("[data-completion-summary]", `
    <div class="portfolio-dashboard">
      <article class="metric-card"><strong>${prototypeState.pathways.length}</strong><span>Prototype options</span></article>
      <article class="metric-card"><strong>${experiments}</strong><span>Experiment cards started</span></article>
      <article class="metric-card"><strong>${prototypeState.pathways.filter(p => p.owners.experimentOwner || p.owners.pathwayOwner).length}</strong><span>Owners named</span></article>
      <article class="metric-card"><strong>${prototypeState.pathways.filter(p => p.reviewDate).length}</strong><span>Review dates</span></article>
    </div>
  `);
}

function updatePrototypeProgress() {
  const sectionsComplete = activePrototypeSections.filter(sectionComplete).length;
  const experiments = prototypeState.pathways.filter(p => p.experiment.title && p.experiment.hypothesis && (p.owners.experimentOwner || p.owners.pathwayOwner)).length;
  setText("[data-prototype-progress-label]", `Prototype Experiment · ${sectionsComplete} of ${activePrototypeSections.length} sections complete`);
  setText("[data-prototype-progress-detail]", `${prototypeState.pathways.length} prototype options · ${experiments} prototype cards ready`);
  setText("[data-prototype-time]", `Approximately ${Math.max(6, 35 - sectionsComplete * 6)} minutes remaining`);
  const fill = document.querySelector("[data-prototype-progress-fill]");
  if (fill) fill.style.width = `${Math.round((sectionsComplete / activePrototypeSections.length) * 100)}%`;
  document.querySelectorAll("[data-prototype-section]").forEach(section => {
    const state = section.querySelector("[data-prototype-state]");
    if (state) state.textContent = sectionComplete(section.dataset.prototypeSection) ? "Complete" : section.open ? "In progress" : "Not started";
  });
}

function sectionComplete(section) {
  const p = activePathway();
  if (!p) return false;
  if (section === "review") return Boolean(p.decisionAnswers.problemClear || p.problemDefinition);
  if (section === "outcome") return Boolean(p.desiredOutcome);
  if (section === "backcast") return p.backcastSteps.length >= 3;
  if (section === "decision") return Boolean(p.decisionOutcome);
  if (section === "interventions") return Boolean(p.selectedInterventionId);
  if (section === "horizons") return p.horizons.every(h => h.objective && h.actions.length);
  if (section === "prototype") return Boolean(p.prototypeType && p.experiment.hypothesis);
  if (section === "ownership") return Boolean((p.owners.experimentOwner || p.owners.pathwayOwner) && p.metrics.length && p.risks.length && p.reviewDate);
  if (section === "summary") return Boolean(p.completed);
  return false;
}

function defaultHorizons(problem) {
  return [
    { type: "h1", title: "Horizon 1", timeframe: "0–3 months", objective: "Test or improve the current system", actions: ["Clarify owner", "Run a small prototype"], owner: "", participants: [], resources: [], dependencies: [], measures: [], decisionDate: "" },
    { type: "h2", title: "Horizon 2", timeframe: "3–12 months", objective: "Develop and integrate the emerging pathway", actions: ["Expand pilot", "Build capability"], owner: "", participants: [], resources: [], dependencies: [], measures: [], decisionDate: "" },
    { type: "h3", title: "Horizon 3", timeframe: "12+ months", objective: "Create wider strategic or transformational change", actions: ["Scale learning", "Build long-term partnerships"], owner: "", participants: [], resources: [], dependencies: [], measures: [], decisionDate: "" }
  ];
}

function defaultExperiment(problem, family) {
  return {
    title: `${family} prototype for ${problem.title || "priority problem"}`,
    hypothesis: `If we test a ${family} intervention for the affected teams or stakeholders, then we will improve decision confidence because the riskiest assumption can be observed before scaling.`,
    learningObjective: "Reduce uncertainty about feasibility, stakeholder response and evidence quality.",
    method: "Run a contained pilot, collect qualitative and quantitative evidence, and review results against decision thresholds.",
    decisionThreshold: "Proceed if evidence improves and risks remain acceptable; iterate if assumptions are partly supported; pause or return to discovery if evidence contradicts the pathway.",
    startDate: "",
    endDate: "",
    status: "draft"
  };
}

function defaultMetrics(problem) {
  return [
    { name: "Evidence confidence improved", category: "learning", target: "Confidence increases by one level", owner: "" },
    { name: "Prototype completed", category: "activity", target: "One contained test completed", owner: "" },
    { name: "Stakeholder response understood", category: "outcome", target: "Key feedback captured", owner: "" }
  ];
}

function defaultRisks(problem) {
  return [
    { category: "operational", description: "Prototype disrupts normal work", likelihood: 2, severity: 3, mitigation: "Limit scope and agree review point" },
    { category: "data", description: "Evidence remains incomplete", likelihood: 3, severity: 3, mitigation: "Define minimum evidence threshold" }
  ];
}

function generateInterventions(problem, family) {
  const options = [
    option(problem, family, `${titleCase(family)} pilot`, `Test a focused ${family} intervention linked to the selected problem.`, "Reduce uncertainty through a contained learning activity", 4, 3, 2),
    option(problem, "governance", "Ownership and decision-rights redesign", "Clarify who owns decisions, evidence and escalation.", "Improve accountability and decision speed", 3, 2, 2),
    option(problem, "data", "Evidence visibility sprint", "Improve the minimum data needed to make a responsible decision.", "Increase confidence before scaling", 3, 2, 1)
  ];
  if (problem.cynefin === "complex") options.push(option(problem, "collaboration", "Stakeholder safe-to-fail experiment", "Invite affected groups into a contained experiment and learning review.", "Observe patterns before committing to a single solution", 4, 4, 3));
  return options;
}

function option(problem, family, title, description, mechanism, impact, effort, risk) {
  return { id: `option-${Date.now()}-${Math.random().toString(16).slice(2)}`, family, title, description, mechanism, impact, effort, risk, status: "suggested", tools: toolSuggestions(family) };
}

function recommendedFamily(problem) {
  const text = `${problem.title} ${problem.description} ${problem.cluster || ""}`.toLowerCase();
  if (text.includes("data") || text.includes("evidence")) return "data";
  if (text.includes("supplier")) return "supply-chain";
  if (text.includes("governance") || text.includes("ownership")) return "governance";
  if (text.includes("culture") || text.includes("employee")) return "behaviour";
  if (text.includes("product") || text.includes("packaging")) return "product";
  return "process";
}

function recommendedPrototype(problem, family) {
  if (problem.cynefin === "complex") return "behaviour";
  if (family === "data") return "digital";
  if (family === "supply-chain") return "supply-chain";
  if (family === "product") return "product";
  if (family === "governance") return "organisational";
  return family === "policy" ? "policy" : "process";
}

function nextRoute(problem) {
  if (problem.cynefin === "complex" || (problem.archetypes || []).includes("experiment-first")) return "experiment";
  if (problem.cynefin === "confused" || problem.confidence <= 2) return "return-to-discovery";
  if (problem.scores?.readiness <= 2) return "build-capability";
  if (problem.cynefin === "chaotic") return "stabilise";
  return "proceed";
}

function decisionRationale(route, problem) {
  if (route === "experiment") return "Experiment is recommended because uncertainty, stakeholders or system behaviour may affect outcomes.";
  if (route === "return-to-discovery") return "More evidence is needed before selecting an intervention.";
  if (route === "build-capability") return "Capability or ownership must improve before the intervention can work.";
  if (route === "stabilise") return "Immediate stabilisation should happen before deeper analysis.";
  return "The problem appears clear enough to proceed to structured planning.";
}

function outcomeQuality(p) {
  const flags = [];
  if (!p.desiredOutcome) flags.push("Missing desired outcome");
  if (p.desiredOutcome && p.desiredOutcome.length < 50) flags.push("May be too vague");
  if (!p.beneficiaries.length) flags.push("Missing stakeholder");
  if (!p.timeframe) flags.push("Missing timeframe");
  if (!flags.length) flags.push("Clear enough to continue");
  return flags;
}

function portfolioWarnings() {
  const primary = prototypeState.pathways.filter(p => prototypeState.primaryIds.includes(p.id));
  const warnings = [];
  const missingOwner = primary.filter(p => !p.owners.pathwayOwner).length;
  if (missingOwner) warnings.push(`${missingOwner} primary pathway${missingOwner === 1 ? "" : "s"} still need a pathway owner.`);
  if (primary.every(p => p.prototypeType !== "behaviour" && p.prototypeType !== "community")) warnings.push("The portfolio contains no explicit Human Empathy or participation prototype.");
  if (primary.filter(p => p.decisionOutcome === "experiment").length === 0) warnings.push("The portfolio contains no low-risk learning experiment.");
  if (primary.filter(p => p.owners.dataOwner).length > 1) warnings.push("Several pathways may depend on the same data capacity.");
  return warnings;
}

function summaryValue(p, label, option) {
  const h = Object.fromEntries(p.horizons.map(h => [h.title, h]));
  const map = {
    "Problem": p.title,
    "Desired Outcome": p.desiredOutcome || "Not defined",
    "Decision": titleCase(p.decisionOutcome),
    "Intervention": option?.title || "Not selected",
    "Horizon 1": h["Horizon 1"]?.actions.join("; ") || "Missing",
    "Horizon 2": h["Horizon 2"]?.actions.join("; ") || "Missing",
    "Horizon 3": h["Horizon 3"]?.actions.join("; ") || "Missing",
    "Experiment": p.experiment.title || "Missing",
    "Review": p.reviewDate || "Missing",
    "Learn": p.experiment.learningObjective || "Missing"
  };
  return map[label] || "";
}

function radioCard(name, value, current) {
  return `<label class="select-card"><input type="radio" name="${name}" value="${value}" ${current === value ? "checked" : ""}><span>${titleCase(value)}</span><small>${value}</small></label>`;
}

function radioPill(name, value, current) {
  return `<label><input type="radio" name="${name}" value="${value}" ${current === value ? "checked" : ""}>${titleCase(value)}</label>`;
}

function checkChip(name, value, selected) {
  return `<label><input type="checkbox" name="${name}" value="${value}" ${(selected || []).includes(value) ? "checked" : ""}>${titleCase(value)}</label>`;
}

function toolSuggestions(family) {
  const map = {
    data: ["data dictionary", "responsibility matrix", "reporting workflow"],
    "supply-chain": ["supplier engagement", "Scope 3 mapping", "traceability test"],
    governance: ["decision tree", "governance mapping", "RACI"],
    behaviour: ["behavioural research", "stakeholder interviews", "safe-to-fail experiment"],
    product: ["LCA", "material comparison", "product prototype"]
  };
  return map[family] || ["Three Horizons", "Experiment Card", "assumptions mapping"];
}

function savePrototype() {
  clearTimeout(savePrototype.timer);
  const autosave = document.querySelector("[data-prototype-autosave]");
  if (autosave) autosave.textContent = "Saving";
  savePrototype.timer = setTimeout(() => {
    const snapshot = prototypeSnapshot();
    localStorage.setItem(prototypeKey, JSON.stringify(snapshot));
    if (!prototypeBackendReady) {
      if (autosave) autosave.textContent = "Saved locally";
      return;
    }
    savePrototypeBackend(snapshot, "draft").then((result) => {
      if (result?.ok && result.stateId) prototypeState.stateId = result.stateId;
      localStorage.setItem(prototypeKey, JSON.stringify(prototypeSnapshot()));
      if (autosave) autosave.textContent = result?.ok ? "Saved just now" : "Saved locally";
    }).catch(() => {
      if (autosave) autosave.textContent = "Saved locally";
    });
  }, 420);
}

function activeJourneyId() {
  return onboardingData.journeyId || priorityData.journeyId || "anonymous-local";
}

function prototypeSnapshot() {
  const reviewed = Boolean(document.querySelector('[name="prototypeReviewed"]')?.checked || prototypeState.reviewed);
  prototypeState.reviewed = reviewed;
  return {
    stateId: prototypeState.stateId,
    sourcePriorityStateId: prototypeState.sourcePriorityStateId,
    sourcePriorityPortfolioId: prototypeState.sourcePriorityPortfolioId,
    pathways: prototypeState.pathways,
    activeId: prototypeState.activeId,
    primaryIds: prototypeState.primaryIds,
    reviewed,
    carryLearningGaps: Boolean(document.querySelector('[name="carryLearningGaps"]')?.checked)
  };
}

async function hydratePrototypeFromBackend() {
  const autosave = document.querySelector("[data-prototype-autosave]");
  try {
    const response = await fetch(`/api/journeys/${encodeURIComponent(activeJourneyId())}/interventions?anonymousSessionId=${encodeURIComponent(prototypeAnonymousSessionId)}`);
    if (!response.ok) throw new Error("Page 6 state unavailable");
    const data = await response.json();
    const formData = data.formData || {};
    if (data.stateId) prototypeState.stateId = data.stateId;
    if (formData.sourcePriorityStateId) prototypeState.sourcePriorityStateId = formData.sourcePriorityStateId;
    if (formData.sourcePriorityPortfolioId) prototypeState.sourcePriorityPortfolioId = formData.sourcePriorityPortfolioId;
    if ((data.found || (formData.pathways || []).length) && (formData.pathways || []).length) {
      prototypeState.pathways = formData.pathways;
      prototypeState.activeId = formData.activeId || formData.pathways[0]?.id || prototypeState.activeId;
      prototypeState.primaryIds = formData.primaryIds || formData.pathways.slice(0, 3).map((p) => p.id);
      prototypeState.reviewed = Boolean(formData.reviewed);
      const reviewedBox = document.querySelector('[name="prototypeReviewed"]');
      if (reviewedBox) reviewedBox.checked = prototypeState.reviewed;
      const learningBox = document.querySelector('[name="carryLearningGaps"]');
      if (learningBox) learningBox.checked = Boolean(formData.carryLearningGaps);
    }
    prototypeBackendReady = true;
    renderPrototypeAll();
    if (autosave) autosave.textContent = data.found ? "Restored from backend" : "Ready to save";
  } catch (error) {
    prototypeBackendReady = false;
    if (autosave) autosave.textContent = "Saved locally";
  }
}

async function savePrototypeBackend(snapshot, status = "draft") {
  const stateId = snapshot.stateId || prototypeState.stateId;
  const endpoint = stateId
    ? `/api/interventions/${encodeURIComponent(stateId)}/${status === "completed" ? "complete" : "autosave"}`
    : `/api/journeys/${encodeURIComponent(activeJourneyId())}/interventions`;
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      anonymousSessionId: prototypeAnonymousSessionId,
      journeyId: activeJourneyId(),
      status,
      formData: snapshot
    })
  });
  return response.json();
}

document.addEventListener("input", (event) => {
  const p = activePathway();
  if (!p) return;
  if (event.target.dataset.pathField) p[event.target.dataset.pathField] = event.target.value;
  if (event.target.dataset.experimentField) p.experiment[event.target.dataset.experimentField] = event.target.value;
  if (event.target.dataset.ownerField) p.owners[event.target.dataset.ownerField] = event.target.value;
  if (event.target.dataset.backcastField) p.backcastSteps[Number(event.target.closest("[data-backcast]").dataset.backcast)] = event.target.value;
  if (event.target.dataset.horizonField) {
    const h = p.horizons.find(h => h.type === event.target.dataset.horizon);
    if (h) h[event.target.dataset.horizonField] = event.target.dataset.horizonField === "actions" ? event.target.value.split(";").map(s => s.trim()).filter(Boolean) : event.target.value;
  }
  const metric = event.target.closest("[data-metric]");
  if (metric && event.target.dataset.metricField) p.metrics[Number(metric.dataset.metric)][event.target.dataset.metricField] = event.target.value;
  const risk = event.target.closest("[data-risk]");
  if (risk && event.target.dataset.riskField) p.risks[Number(risk.dataset.risk)][event.target.dataset.riskField] = event.target.value;
  renderPanel();
  renderPortfolio();
  renderCompletion();
  updatePrototypeProgress();
  savePrototype();
});

document.addEventListener("change", (event) => {
  const p = activePathway();
  if (!p) return;
  if (event.target.name === "prototypeType") p.prototypeType = event.target.value;
  if (event.target.name?.startsWith("decision-")) p.decisionAnswers[event.target.name.replace("decision-", "")] = event.target.value;
  if (event.target.name === "problemClear") p.decisionAnswers.problemClear = event.target.value;
  if (event.target.name === "beneficiaries") p.beneficiaries = checkedValues("beneficiaries");
  if (event.target.name === "changes") p.changes = checkedValues("changes");
  if (event.target.name === "status") p.status = event.target.value;
  if (event.target.name === "prototypeReviewed") prototypeState.reviewed = event.target.checked;
  renderPrototypeAll();
});

document.addEventListener("click", async (event) => {
  const p = activePathway();
  if (event.target.dataset.openPathway) {
    prototypeState.activeId = event.target.dataset.openPathway;
    renderPrototypeAll();
  }
  if (event.target.dataset.togglePrimary) {
    const id = event.target.dataset.togglePrimary;
    prototypeState.primaryIds = prototypeState.primaryIds.includes(id) ? prototypeState.primaryIds.filter(x => x !== id) : [...prototypeState.primaryIds, id].slice(0, 3);
    renderPrototypeAll();
  }
  if (event.target.matches("[data-prototype-next]")) {
    const current = event.target.closest(".onboarding-section");
    const next = current?.nextElementSibling;
    if (current) current.open = false;
    if (next?.matches(".onboarding-section")) {
      next.open = true;
      next.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    renderPrototypeAll();
  }
  if (event.target.matches("[data-add-backcast]")) {
    p.backcastSteps.push("New required condition");
    renderPrototypeAll();
  }
  if (event.target.dataset.selectOption) {
    p.selectedInterventionId = event.target.dataset.selectOption;
    p.interventionOptions.forEach(o => o.status = o.id === p.selectedInterventionId ? "selected" : o.status);
    renderPrototypeAll();
  }
  if (event.target.dataset.rejectOption) {
    const option = p.interventionOptions.find(o => o.id === event.target.dataset.rejectOption);
    if (option) option.status = "rejected";
    renderPrototypeAll();
  }
  if (event.target.matches("[data-add-intervention]")) {
    p.interventionOptions.push(option(p, "collaboration", "Alternative collaboration pathway", "Explore a partnership-based route before committing internally.", "Share capability and reduce direct-control limits", 3, 3, 2));
    renderPrototypeAll();
  }
  if (event.target.matches("[data-add-metric]")) {
    p.metrics.push({ name: "New metric", category: "learning", target: "", owner: "" });
    renderPrototypeAll();
  }
  if (event.target.matches("[data-add-risk]")) {
    p.risks.push({ category: "risk", description: "New risk", likelihood: 2, severity: 2, mitigation: "" });
    renderPrototypeAll();
  }
  if (event.target.matches("[data-confirm-pathway]")) {
    p.completed = true;
    renderPrototypeAll();
  }
  if (event.target.matches("[data-prototype-resource-toggle]")) {
    const panel = document.querySelector("[data-prototype-resource-panel]");
    if (panel) panel.hidden = !panel.hidden;
  }
  if (event.target.matches("[data-review-priority]")) {
    alert(`Priority portfolio loaded: ${(priorityData.selectedIds || []).length} selected priorities and ${(priorityData.problems || []).length} total problems.`);
  }
  if (event.target.matches("[data-prototype-download]")) {
    const snapshot = prototypeSnapshot();
    if (event.target.dataset.prototypeDownload === "all" && prototypeBackendReady) {
      await savePrototypeBackend(snapshot, prototypeState.reviewed ? "completed" : "draft").then((result) => {
        if (result?.ok && result.stateId) prototypeState.stateId = result.stateId;
      }).catch(() => null);
    }
    const blob = new Blob([JSON.stringify(prototypeSnapshot(), null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `green-spectrum-${event.target.dataset.prototypeDownload}-portfolio.json`;
    link.click();
    URL.revokeObjectURL(url);
  }
  if (event.target.matches("[data-prototype-complete]")) {
    const reviewed = document.querySelector('[name="prototypeReviewed"]');
    if (reviewed && !reviewed.checked) {
      reviewed.focus();
      const autosave = document.querySelector("[data-prototype-autosave]");
      if (autosave) autosave.textContent = "Review confirmation required";
      return;
    }
    const result = await savePrototypeBackend(prototypeSnapshot(), "completed").catch(() => ({ ok: false, error: "Unable to reach backend" }));
    const autosave = document.querySelector("[data-prototype-autosave]");
    if (result?.ok) {
      prototypeState.stateId = result.stateId || prototypeState.stateId;
      localStorage.setItem(prototypeKey, JSON.stringify(prototypeSnapshot()));
      if (autosave) autosave.textContent = "Cycle complete";
    } else if (autosave) {
      const issue = result?.validation?.blockingIssues?.[0] || result?.error || "Completion needs more detail";
      autosave.textContent = issue;
    }
  }
  if (event.target.matches("[data-prototype-save-exit]")) {
    savePrototype();
    window.location.href = "../";
  }
  if (event.target.matches("[data-dismiss-prototype-insight]")) {
    event.target.closest(".generated-insight").hidden = true;
  }
  if (event.target.matches("[data-new-cycle]")) {
    window.location.href = "../onboarding/";
  }
});

function checkedValues(name) {
  return [...document.querySelectorAll(`[name="${name}"]:checked`)].map(input => input.value);
}

function activeText() {
  return activePathway()?.title || "No active pathway";
}

function setHtml(selector, html) {
  const target = document.querySelector(selector);
  if (target) target.innerHTML = html;
}

function setText(selector, value) {
  const target = document.querySelector(selector);
  if (target) target.textContent = value;
}

function titleCase(value) {
  return String(value || "").replaceAll("-", " ").replace(/\b\w/g, l => l.toUpperCase());
}

function escapeHtml(value) {
  return String(value || "").replace(/[&<>"']/g, match => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#039;" }[match]));
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/"/g, "&quot;");
}
