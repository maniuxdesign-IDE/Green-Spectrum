const impactStorageKey = "greenSpectrum.impactJourney.v1";
const impactSessionStorageKey = "greenSpectrum.sessionId.v1";
const onboardingContext = JSON.parse(localStorage.getItem("greenSpectrum.onboarding.v1") || "{}");
const exploreContext = JSON.parse(localStorage.getItem("greenSpectrum.explore.v1") || "{}");
const impactAnonymousSessionId = localStorage.getItem(impactSessionStorageKey) || `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
localStorage.setItem(impactSessionStorageKey, impactAnonymousSessionId);

const layerDefinitions = [
  ["activities", "Key activities", "What happens at each stage?", "Activity title", ["main activity", "resource-intensive activity", "informal or undocumented activity"]],
  ["decisions", "Decisions and control points", "Where are the important decisions made?", "Decision title", ["approval point", "budget choice", "design gate"]],
  ["stakeholders", "Stakeholders", "Who shapes or experiences each stage?", "Stakeholder name", ["supplier", "customer", "operations", "community"]],
  ["data", "Data and evidence", "What evidence exists at each stage?", "Data source", ["energy data", "procurement data", "risk register"]],
  ["environmental", "Environmental impacts", "What environmental impacts occur?", "Environmental impact", ["emissions", "waste", "water", "materials"]],
  ["social", "Social and human impacts", "What human and social impacts occur?", "Social impact", ["working conditions", "customer wellbeing", "community impact"]],
  ["governance", "Governance impacts", "What governance weaknesses appear?", "Issue or strength", ["ownership", "accountability", "transparency"]],
  ["business", "Business and operational impacts", "What business impacts occur?", "Business impact", ["cost", "resilience", "reputation", "supply security"]],
  ["experience", "Experience and behaviour", "What do people experience at each stage?", "Experience", ["frustration", "workaround", "motivation"]],
  ["unknowns", "Assumptions and unknowns", "What do we not yet know?", "Unknown or assumption", ["missing information", "expert input needed", "operational data needed"]],
  ["strengths", "Strengths and capabilities", "What is already working well?", "Strength", ["good evidence", "strong relationship", "reliable process"]]
];

const stageTemplates = {
  "product-value-chain": ["Raw materials", "Procurement", "Production", "Distribution", "Use", "End of life"],
  "service-journey": ["Need identified", "Access", "Service delivery", "Use or participation", "Follow-up", "Long-term outcome"],
  "supply-chain": ["Supplier selection", "Sourcing", "Transport", "Processing", "Distribution", "Supplier review"],
  "operating-process": ["Issue identified", "Evidence gathered", "Proposal developed", "Approval", "Implementation", "Review"],
  "customer-journey": ["Need or trigger", "Discovery", "Purchase or access", "Use", "Support", "Long-term relationship"],
  "decision-journey": ["Issue identified", "Evidence gathered", "Proposal developed", "Approval", "Implementation", "Review"],
  "place-based-system": ["Place context", "Actors and assets", "Flows and dependencies", "Pressure points", "Intervention context", "Long-term stewardship"],
  "custom": ["Start", "Middle stage", "Decision point", "Delivery", "Outcome", "Review"]
};

const savedImpact = JSON.parse(localStorage.getItem(impactStorageKey) || "{}");
const impactState = {
  stateId: savedImpact.stateId || "",
  stages: savedImpact.stages || [],
  activeLayer: savedImpact.activeLayer || "activities",
  activeStage: savedImpact.activeStage || "",
  layerItems: savedImpact.layerItems || {},
  relationships: savedImpact.relationships || [],
  problemSignals: savedImpact.problemSignals || [],
  opportunities: savedImpact.opportunities || []
};

const impactForm = document.querySelector("[data-impact-form]");
const stageBuilder = document.querySelector("[data-stage-builder]");
const layerNavigator = document.querySelector("[data-layer-navigator]");
const stageTabs = document.querySelector("[data-stage-tabs]");
const board = document.querySelector("[data-journey-board]");
const autosave = document.querySelector("[data-impact-autosave]");

document.querySelector("[data-impact-organisation]").textContent = onboardingContext.organisationName || "New journey";
renderImportedSignals();
initialiseImpact();
hydrateFromBackend();

function initialiseImpact() {
  if (!impactState.stages.length) generateStages(false);
  renderStages();
  renderLayerNavigator();
  renderBoard();
  renderRelationships();
  updateImpactAnalysis();
  hydrateScopeFields();
}

function hydrateScopeFields() {
  Object.entries(savedImpact.scope || {}).forEach(([key, value]) => {
    const radios = impactForm.querySelectorAll(`[name="${CSS.escape(key)}"]`);
    const matchingRadio = [...radios].find((item) => item.value === value);
    if (matchingRadio && matchingRadio.type === "radio") matchingRadio.checked = true;
    const field = impactForm.querySelector(`[name="${CSS.escape(key)}"]:not([type="radio"])`);
    if (field) field.value = value;
  });
}

function renderImportedSignals() {
  const target = document.querySelector("[data-imported-signals]");
  if (!target) return;
  const responses = Object.values(exploreContext.responses || {});
  const imported = responses
    .filter((response) => ["white", "light", "unknown"].includes(response.maturity))
    .slice(0, 5)
    .map((response) => `${response.area || "Explore signal"} needs deeper mapping`);
  target.innerHTML = `
    <div class="inline-insight">
      <strong>Explore findings carried forward</strong>
      <p>${imported.length ? "Select or edit these signals as mapping prompts." : "No Explore signals found yet. You can add mapping prompts manually."}</p>
      <div class="chip-grid large">${(imported.length ? imported : ["Add a new signal during mapping"]).map((signal, index) => `<label><input type="checkbox" name="importedSignals" value="${escapeAttr(signal)}" ${index < 2 ? "checked" : ""}>${signal}</label>`).join("")}</div>
    </div>
  `;
}

function generateStages(overwrite = true) {
  if (!overwrite && impactState.stages.length) return;
  const selected = impactForm.querySelector('[name="journeyType"]:checked')?.value || savedImpact.scope?.journeyType || inferJourneyType();
  const names = stageTemplates[selected] || stageTemplates.custom;
  impactState.stages = names.map((name, index) => ({
    id: `stage-${Date.now()}-${index}`,
    name,
    description: suggestedDescription(name),
    owner: index === 1 ? "Procurement or operations" : "",
    confidence: "medium",
    source: "system-suggested"
  }));
  impactState.activeStage = impactState.stages[0]?.id || "";
  saveImpact();
}

function inferJourneyType() {
  const industry = (onboardingContext.industry || "").toLowerCase();
  const outputs = Array.isArray(onboardingContext.outputs) ? onboardingContext.outputs.join(" ").toLowerCase() : "";
  if (industry.includes("manufacturing") || industry.includes("food") || outputs.includes("impact map")) return "product-value-chain";
  if (industry.includes("professional") || industry.includes("public")) return "service-journey";
  return "product-value-chain";
}

function suggestedDescription(name) {
  return `Suggested stage for ${name.toLowerCase()}. Confirm, edit or replace before treating it as accurate.`;
}

function renderStages() {
  stageBuilder.innerHTML = impactState.stages.map((stage, index) => `
    <article class="stage-edit-card" data-stage="${stage.id}">
      <span class="confidence-badge">${stage.source === "system-suggested" ? "System-suggested" : "User-confirmed"}</span>
      <label>Stage ${index + 1} name <input value="${escapeAttr(stage.name)}" data-stage-field="name"></label>
      <label>Description <textarea rows="2" data-stage-field="description">${escapeHtml(stage.description || "")}</textarea></label>
      <div class="form-grid">
        <label class="field-label">Owner or lead function <input value="${escapeAttr(stage.owner || "")}" data-stage-field="owner"></label>
        <label class="field-label">Confidence <select data-stage-field="confidence"><option ${stage.confidence === "high" ? "selected" : ""}>high</option><option ${stage.confidence === "medium" ? "selected" : ""}>medium</option><option ${stage.confidence === "low" ? "selected" : ""}>low</option><option ${stage.confidence === "assumption" ? "selected" : ""}>assumption</option></select></label>
      </div>
      <div class="stage-card-actions">
        <button type="button" data-move-stage="up">Move up</button>
        <button type="button" data-move-stage="down">Move down</button>
        <button type="button" data-duplicate-stage>Duplicate</button>
        <button type="button" data-delete-stage>Delete</button>
      </div>
    </article>
  `).join("");
  updateStageSelects();
  renderStageTabs();
  renderMiniMap();
}

function renderLayerNavigator() {
  layerNavigator.innerHTML = layerDefinitions.map(([key, title], index) => `
    <button type="button" class="${impactState.activeLayer === key ? "active" : ""}" data-layer="${key}">
      <span class="layer-number">${String(index + 1).padStart(2, "0")}</span>
      <span class="layer-copy">
        <b>${title}</b>
        <small>${layerStatus(key)}</small>
      </span>
    </button>
  `).join("");
}

function renderStageTabs() {
  stageTabs.innerHTML = impactState.stages.map((stage) => `
    <button type="button" class="${impactState.activeStage === stage.id ? "active" : ""}" data-stage-tab="${stage.id}">${stage.name}</button>
  `).join("");
}

function renderBoard() {
  if (!impactState.activeStage && impactState.stages[0]) impactState.activeStage = impactState.stages[0].id;
  const stage = impactState.stages.find((item) => item.id === impactState.activeStage) || impactState.stages[0];
  const layer = layerDefinitions.find(([key]) => key === impactState.activeLayer) || layerDefinitions[0];
  if (!stage || !layer) {
    board.innerHTML = "<p>Add at least three stages to begin mapping.</p>";
    return;
  }
  const items = getLayerItems(stage.id, layer[0]);
  board.innerHTML = `
    <div class="board-layer-header">
      <div><p class="eyebrow">${stage.name}</p><h3>${layer[1]}</h3><p>${layer[2]}</p></div>
      <button class="button button-secondary" type="button" data-add-layer-item>Add item</button>
    </div>
    <div class="layer-item-list">
      ${items.map((item, index) => renderLayerItem(item, index, layer)).join("") || `<p class="empty-board">No ${layer[1].toLowerCase()} mapped yet. Use the button above to add one, or accept the system suggestion below.</p>`}
    </div>
    <div class="inline-insight"><strong>Suggested prompts</strong><p>${layer[4].join("; ")}.</p><button type="button" class="button button-secondary" data-add-suggestion>Add suggested item</button></div>
  `;
}

function renderLayerItem(item, index, layer) {
  return `
    <article class="layer-item" data-layer-item="${item.id}">
      <label>${layer[3]} <input value="${escapeAttr(item.title)}" data-item-field="title"></label>
      <label>Notes <textarea rows="2" data-item-field="notes">${escapeHtml(item.notes || "")}</textarea></label>
      <div class="form-grid">
        <label class="field-label">Source <input value="${escapeAttr(item.source || "")}" data-item-field="source"></label>
        <label class="field-label">Confidence <select data-item-field="confidence"><option ${item.confidence === "high" ? "selected" : ""}>high</option><option ${item.confidence === "medium" ? "selected" : ""}>medium</option><option ${item.confidence === "low" ? "selected" : ""}>low</option><option ${item.confidence === "assumption" ? "selected" : ""}>assumption</option></select></label>
      </div>
      <small>${item.status || "User-confirmed"} · item ${index + 1}</small>
      <button type="button" data-delete-layer-item>Remove</button>
    </article>
  `;
}

function getLayerItems(stageId, layerKey) {
  impactState.layerItems[stageId] = impactState.layerItems[stageId] || {};
  impactState.layerItems[stageId][layerKey] = impactState.layerItems[stageId][layerKey] || [];
  return impactState.layerItems[stageId][layerKey];
}

function addLayerItem(suggested = false) {
  const stage = impactState.activeStage || impactState.stages[0]?.id;
  const layer = layerDefinitions.find(([key]) => key === impactState.activeLayer);
  if (!stage || !layer) return;
  const items = getLayerItems(stage, layer[0]);
  items.push({
    id: `item-${Date.now()}`,
    title: suggested ? layer[4][items.length % layer[4].length] : "",
    notes: "",
    source: suggested ? "system suggestion" : "",
    confidence: suggested ? "low" : "medium",
    status: suggested ? "System-suggested" : "User-confirmed"
  });
  renderBoard();
  updateImpactAnalysis();
  saveImpact();
}

function updateStageSelects() {
  document.querySelectorAll("[data-stage-select]").forEach((select) => {
    select.innerHTML = impactState.stages.map((stage) => `<option value="${stage.id}">${stage.name}</option>`).join("");
  });
}

function renderRelationships() {
  const target = document.querySelector("[data-relationship-list]");
  if (!target) return;
  target.innerHTML = impactState.relationships.length ? impactState.relationships.map((relationship) => `
    <article class="relationship-card">
      <strong>${stageName(relationship.source)} → ${relationship.type} → ${stageName(relationship.target)}</strong>
      <p>${relationship.description || "No description added."}</p>
      <small>${relationship.confidence} confidence</small>
    </article>
  `).join("") : "<p>No relationships added yet. Add dependencies, feedback loops, bottlenecks or flows once stages exist.</p>";
}

function generateProblemSignals() {
  const signals = [];
  impactState.stages.forEach((stage) => {
    const stageItems = impactState.layerItems[stage.id] || {};
    const unknowns = (stageItems.unknowns || []).length;
    const risks = ["environmental", "social", "governance", "business"].reduce((sum, key) => sum + (stageItems[key] || []).length, 0);
    if (unknowns || risks > 2) {
      signals.push({
        id: `signal-${stage.id}`,
        title: `${stage.name} may need deeper prioritisation`,
        description: `${stage.name} contains ${risks} impact items and ${unknowns} uncertainty items, leading to a need for structured comparison on the next page.`,
        confidence: unknowns ? "low" : "medium",
        source: "journey-generated"
      });
    }
  });
  impactState.problemSignals = mergeByTitle([...impactState.problemSignals, ...signals]);
  renderSignals();
  updateImpactAnalysis();
  saveImpact();
}

function renderSignals() {
  const target = document.querySelector("[data-impact-problem-signals]");
  if (!target) return;
  target.innerHTML = impactState.problemSignals.length ? impactState.problemSignals.map((signal) => `
    <article class="problem-signal" data-signal="${signal.id}">
      <label>Problem signal <input value="${escapeAttr(signal.title)}" data-signal-field="title"></label>
      <textarea rows="2" data-signal-field="description">${escapeHtml(signal.description)}</textarea>
      <small>${signal.source} · ${signal.confidence} confidence</small>
    </article>
  `).join("") : "<p>No problem signals generated yet. Add impacts, unknowns or relationships first.</p>";
}

function renderOpportunities() {
  const target = document.querySelector("[data-opportunity-areas]");
  if (!target) return;
  target.innerHTML = impactState.opportunities.length ? impactState.opportunities.map((item) => `
    <article class="problem-signal" data-opportunity="${item.id}">
      <label>Opportunity area <input value="${escapeAttr(item.title)}" data-opportunity-field="title"></label>
      <textarea rows="2" data-opportunity-field="description">${escapeHtml(item.description || "")}</textarea>
      <small>Unranked · ${item.confidence} confidence</small>
    </article>
  `).join("") : "<p>No opportunity areas added yet. Capture leverage areas without ranking them.</p>";
}

function updateImpactAnalysis() {
  const complete = completionCount();
  const impacts = countLayers(["environmental", "social", "governance", "business"]);
  const gaps = countLayers(["unknowns"]);
  const activities = countLayers(["activities"]);
  setText("[data-impact-progress-label]", `Impact Journey Mapping · ${complete} of 7 sections complete`);
  setText("[data-impact-progress-detail]", `${impactState.stages.length} stages mapped · ${impacts} impacts identified`);
  setText("[data-impact-time]", `Approximately ${Math.max(8, 60 - complete * 7)} minutes remaining`);
  const fill = document.querySelector("[data-impact-progress-fill]");
  if (fill) fill.style.width = `${Math.round((complete / 7) * 100)}%`;

  document.querySelectorAll("[data-impact-section]").forEach((section) => {
    const state = section.querySelector("[data-impact-state]");
    if (!state) return;
    state.textContent = sectionComplete(section.dataset.impactSection) ? "Complete" : section.open ? "In progress" : "Not started";
  });

  const summary = document.querySelector("[data-impact-summary]");
  if (summary) {
    summary.innerHTML = [
      ["Current stage count", `${impactState.stages.length} stages`],
      ["Activities count", `${activities} activities`],
      ["Impact count", `${impacts} impacts`],
      ["Problem-signal count", `${impactState.problemSignals.length} signals`],
      ["Evidence-gap count", `${gaps} unknowns`],
      ["Recommended next layer", nextLayerRecommendation()]
    ].map(([label, value]) => `<div class="summary-row"><dt>${label}</dt><dd>${value}</dd></div>`).join("");
  }
  const insight = document.querySelector("[data-impact-insight] p");
  if (insight) insight.textContent = latestInsight();
  renderAnalysisLists();
  renderResults();
  renderLayerNavigator();
}

function renderAnalysisLists() {
  list("[data-impact-hotspots]", hotspotStages(), "Hotspots will appear after impact layers are populated.");
  list("[data-leverage-areas]", impactState.relationships.map((rel) => `${stageName(rel.source)} affects ${stageName(rel.target)} through ${rel.type}.`), "Add relationships to reveal leverage areas.");
  list("[data-bottlenecks]", impactState.relationships.filter((rel) => rel.type.toLowerCase().includes("bottleneck") || rel.type.toLowerCase().includes("delay")).map((rel) => `${stageName(rel.source)} may slow ${stageName(rel.target)}.`), "No bottlenecks recorded yet.");
  list("[data-impact-evidence-gaps]", evidenceGapItems(), "No evidence gaps recorded yet.");
  list("[data-stakeholder-blindspots]", blindspots(), "Stakeholder blind spots will appear after stakeholder mapping.");
  list("[data-priority-questions]", priorityQuestions(), "Priority questions will appear as the map develops.");
}

function renderResults() {
  renderMiniMap();
  const heatmap = document.querySelector("[data-impact-heatmap]");
  if (heatmap) {
    heatmap.innerHTML = impactState.stages.map((stage) => {
      const count = ["environmental", "social", "governance", "business"].reduce((sum, key) => sum + getLayerItems(stage.id, key).length, 0);
      return `<span class="${count > 4 ? "high" : count > 1 ? "medium" : "low"}">${stage.name}<b>${count}</b></span>`;
    }).join("");
  }
  list("[data-stakeholder-summary]", impactState.stages.flatMap((stage) => getLayerItems(stage.id, "stakeholders").map((item) => `${item.title || "Unnamed stakeholder"} · ${stage.name}`)), "No stakeholders mapped yet.");
  setText("[data-analysis-summary]", latestInsight());
}

function renderMiniMap() {
  const target = document.querySelector("[data-mini-journey-map]");
  if (!target) return;
  target.innerHTML = impactState.stages.map((stage, index) => `<article><span>${index + 1}</span><strong>${stage.name}</strong><small>${stage.confidence} confidence</small></article>`).join("");
}

function completionCount() {
  return ["scope", "stages", "board", "relationships", "signals", "analysis", "results"].filter(sectionComplete).length;
}

function sectionComplete(section) {
  if (section === "scope") return Boolean(scope().journeyType && scope().startPoint && scope().endPoint);
  if (section === "stages") return impactState.stages.length >= 3 && impactState.stages.length <= 8;
  if (section === "board") return impactState.stages.length >= 3 && impactState.stages.every((stage) => getLayerItems(stage.id, "activities").length);
  if (section === "relationships") return impactState.relationships.length > 0;
  if (section === "signals") return impactState.problemSignals.length > 0 || impactState.opportunities.length > 0;
  if (section === "analysis") return countLayers(["environmental", "social", "governance", "business", "unknowns"]) > 0;
  if (section === "results") return document.querySelector('[name="mapReviewed"]')?.checked;
  return false;
}

function countLayers(layerKeys) {
  return impactState.stages.reduce((sum, stage) => sum + layerKeys.reduce((inner, key) => inner + getLayerItems(stage.id, key).length, 0), 0);
}

function scope() {
  const formData = new FormData(impactForm);
  return Object.fromEntries([...formData.entries()].filter(([, value]) => typeof value === "string"));
}

function saveImpact() {
  clearTimeout(saveImpact.timer);
  if (autosave) autosave.textContent = "Saving";
  saveImpact.timer = setTimeout(() => {
    const snapshot = { ...impactState, scope: scope(), savedAt: new Date().toISOString() };
    localStorage.setItem(impactStorageKey, JSON.stringify(snapshot));
    saveImpactBackend(snapshot).then((saved) => {
      if (saved?.stateId) {
        impactState.stateId = saved.stateId;
        localStorage.setItem(impactStorageKey, JSON.stringify({ ...snapshot, stateId: saved.stateId }));
      }
      if (autosave) autosave.textContent = saved?.ok === false ? "Saved locally" : "Saved just now";
    });
  }, 240);
}

function activeJourneyId() {
  return onboardingContext.journeyId || savedImpact.journeyId || "anonymous-local";
}

async function hydrateFromBackend() {
  try {
    const response = await fetch(`/api/journeys/${encodeURIComponent(activeJourneyId())}/impact-journey?anonymousSessionId=${encodeURIComponent(impactAnonymousSessionId)}`);
    if (!response.ok) return;
    const data = await response.json();
    if (!data.found || !data.formData) return;
    Object.assign(impactState, data.formData, { stateId: data.stateId || impactState.stateId });
    localStorage.setItem(impactStorageKey, JSON.stringify({ ...impactState, scope: data.formData.scope || {}, savedAt: data.updatedAt }));
    hydrateScopeFields();
    renderStages();
    renderLayerNavigator();
    renderBoard();
    renderRelationships();
    renderSignals();
    renderOpportunities();
    updateImpactAnalysis();
  } catch (error) {
    console.warn("Impact Journey backend restore unavailable", error);
  }
}

async function saveImpactBackend(snapshot, status = "draft") {
  try {
    const endpoint = impactState.stateId
      ? `/api/impact-journeys/${encodeURIComponent(impactState.stateId)}/${status === "completed" ? "complete" : "autosave"}`
      : `/api/journeys/${encodeURIComponent(activeJourneyId())}/impact-journey`;
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        anonymousSessionId: impactAnonymousSessionId,
        journeyId: activeJourneyId(),
        impactJourneyStateId: impactState.stateId || undefined,
        status,
        formData: snapshot
      })
    });
    return response.ok ? response.json() : { ok: false };
  } catch (error) {
    console.warn("Impact Journey backend save unavailable", error);
    return { ok: false };
  }
}

function stageName(id) {
  return impactState.stages.find((stage) => stage.id === id)?.name || "Unknown stage";
}

function layerStatus(layerKey) {
  const count = impactState.stages.reduce((sum, stage) => sum + getLayerItems(stage.id, layerKey).length, 0);
  return count ? `${count} mapped` : layerKey === "activities" ? "Start here" : "Not started";
}

function nextLayerRecommendation() {
  const missing = layerDefinitions.find(([key]) => !impactState.stages.some((stage) => getLayerItems(stage.id, key).length));
  return missing ? missing[1] : "Review analysis";
}

function latestInsight() {
  const hotspots = hotspotStages();
  if (hotspots.length) return `${hotspots[0]} This is based on mapped impacts and should be checked against confidence and evidence.`;
  if (impactState.relationships.length) return `${stageName(impactState.relationships[0].source)} appears connected to ${stageName(impactState.relationships[0].target)} through ${impactState.relationships[0].type}.`;
  if (impactState.stages.length >= 3) return "The journey structure is ready. Populate activities first, then add evidence and impacts layer by layer.";
  return "Define scope and stages to start building the system map.";
}

function hotspotStages() {
  return impactState.stages.map((stage) => {
    const count = ["environmental", "social", "governance", "business"].reduce((sum, key) => sum + getLayerItems(stage.id, key).length, 0);
    return count ? `${stage.name} contains ${count} mapped impact item${count === 1 ? "" : "s"}.` : "";
  }).filter(Boolean).sort((a, b) => Number(b.match(/\d+/)?.[0] || 0) - Number(a.match(/\d+/)?.[0] || 0));
}

function evidenceGapItems() {
  return impactState.stages.flatMap((stage) => getLayerItems(stage.id, "unknowns").map((item) => `${stage.name}: ${item.title || "Unknown"}`));
}

function blindspots() {
  return impactState.stages.filter((stage) => !getLayerItems(stage.id, "stakeholders").length).map((stage) => `${stage.name} has no stakeholders mapped yet.`);
}

function priorityQuestions() {
  const questions = [];
  if (countLayers(["unknowns"]) > 0) questions.push("Which evidence gaps materially affect confidence?");
  if (countLayers(["environmental", "social", "governance", "business"]) > 5) questions.push("Which impact areas deserve comparison by urgency and strategic relevance?");
  if (impactState.relationships.length) questions.push("Which dependencies may create the strongest leverage?");
  return questions;
}

function mergeByTitle(items) {
  return [...new Map(items.map((item) => [item.title, item])).values()];
}

function list(selector, items, fallback) {
  const target = document.querySelector(selector);
  if (!target) return;
  target.innerHTML = items.length ? items.map((item) => `<li>${item}</li>`).join("") : `<li>${fallback}</li>`;
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

impactForm.addEventListener("input", (event) => {
  const stageCard = event.target.closest("[data-stage]");
  if (stageCard) {
    const stage = impactState.stages.find((item) => item.id === stageCard.dataset.stage);
    if (stage) {
      stage[event.target.dataset.stageField] = event.target.value;
      stage.source = "user-confirmed";
      renderStageTabs();
      renderMiniMap();
      updateStageSelects();
    }
  }
  const itemCard = event.target.closest("[data-layer-item]");
  if (itemCard) {
    const items = getLayerItems(impactState.activeStage, impactState.activeLayer);
    const item = items.find((entry) => entry.id === itemCard.dataset.layerItem);
    if (item) item[event.target.dataset.itemField] = event.target.value;
  }
  updateImpactAnalysis();
  saveImpact();
});

impactForm.addEventListener("change", () => {
  const scopeData = scope();
  const interpretation = document.querySelector("[data-scope-interpretation]");
  if (interpretation) {
    interpretation.textContent = scopeData.journeyType && scopeData.startPoint && scopeData.endPoint
      ? `You are mapping ${scopeData.journeyType.replaceAll("-", " ")} from ${scopeData.startPoint} to ${scopeData.endPoint}.`
      : "Define the journey type, start and end points to generate suggested stages.";
  }
  updateImpactAnalysis();
  saveImpact();
});

document.addEventListener("click", (event) => {
  const target = event.target;
  if (target.matches("[data-generate-stages]")) {
    generateStages(true);
    renderStages();
    renderBoard();
    updateImpactAnalysis();
  }
  if (target.matches("[data-add-stage]")) {
    if (impactState.stages.length >= 8) return;
    impactState.stages.push({ id: `stage-${Date.now()}`, name: "New stage", description: "", owner: "", confidence: "medium", source: "user-confirmed" });
    impactState.activeStage = impactState.stages.at(-1).id;
    renderStages();
    renderBoard();
    updateImpactAnalysis();
    saveImpact();
  }
  if (target.matches("[data-build-board]")) {
    document.querySelector("#journey-board-orientation").open = true;
    document.querySelector("#journey-board-orientation").scrollIntoView({ behavior: "smooth", block: "center" });
  }
  if (target.matches("[data-layer]")) {
    impactState.activeLayer = target.dataset.layer;
    renderLayerNavigator();
    renderBoard();
    saveImpact();
  }
  if (target.matches("[data-stage-tab]")) {
    impactState.activeStage = target.dataset.stageTab;
    renderStageTabs();
    renderBoard();
    saveImpact();
  }
  if (target.matches("[data-add-layer-item]")) addLayerItem(false);
  if (target.matches("[data-add-suggestion]")) addLayerItem(true);
  if (target.matches("[data-delete-layer-item]")) {
    const card = target.closest("[data-layer-item]");
    const items = getLayerItems(impactState.activeStage, impactState.activeLayer);
    impactState.layerItems[impactState.activeStage][impactState.activeLayer] = items.filter((item) => item.id !== card.dataset.layerItem);
    renderBoard();
    updateImpactAnalysis();
    saveImpact();
  }
  const stageCard = target.closest("[data-stage]");
  if (target.matches("[data-delete-stage]") && impactState.stages.length > 3) {
    impactState.stages = impactState.stages.filter((stage) => stage.id !== stageCard.dataset.stage);
    impactState.activeStage = impactState.stages[0]?.id || "";
    renderStages();
    renderBoard();
    updateImpactAnalysis();
    saveImpact();
  }
  if (target.matches("[data-duplicate-stage]")) {
    const stage = impactState.stages.find((item) => item.id === stageCard.dataset.stage);
    if (stage && impactState.stages.length < 8) {
      impactState.stages.push({ ...stage, id: `stage-${Date.now()}`, name: `${stage.name} copy`, source: "user-confirmed" });
      renderStages();
      saveImpact();
    }
  }
  if (target.matches("[data-move-stage]")) {
    const index = impactState.stages.findIndex((stage) => stage.id === stageCard.dataset.stage);
    const direction = target.dataset.moveStage === "up" ? -1 : 1;
    const nextIndex = index + direction;
    if (nextIndex >= 0 && nextIndex < impactState.stages.length) {
      const [stage] = impactState.stages.splice(index, 1);
      impactState.stages.splice(nextIndex, 0, stage);
      renderStages();
      saveImpact();
    }
  }
  if (target.matches("[data-add-relationship]")) {
    const data = scope();
    impactState.relationships.push({
      id: `relationship-${Date.now()}`,
      source: data.relationshipSource,
      target: data.relationshipTarget,
      type: data.relationshipType,
      description: data.relationshipDescription,
      confidence: data.relationshipConfidence || "medium"
    });
    renderRelationships();
    updateImpactAnalysis();
    saveImpact();
  }
  if (target.matches("[data-generate-signals]")) generateProblemSignals();
  if (target.matches("[data-add-opportunity]")) {
    impactState.opportunities.push({ id: `opp-${Date.now()}`, title: "New opportunity area", description: "Describe where change could create value without ranking it yet.", confidence: "low" });
    renderOpportunities();
    updateImpactAnalysis();
    saveImpact();
  }
  if (target.matches("[data-impact-next]")) {
    const current = target.closest(".onboarding-section");
    const next = current?.nextElementSibling;
    if (current) current.open = false;
    if (next?.matches(".onboarding-section")) {
      next.open = true;
      next.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    updateImpactAnalysis();
    saveImpact();
  }
  if (target.matches("[data-impact-resource-toggle]")) {
    const panel = document.querySelector("[data-impact-resource-panel]");
    if (panel) panel.hidden = !panel.hidden;
  }
  if (target.matches("[data-impact-review-explore]")) {
    alert(`Explore outputs found: ${Object.keys(exploreContext.responses || {}).length} maturity responses and ${(exploreContext.problemSignals || []).length} saved problem signals.`);
  }
  if (target.matches("[data-impact-download]")) {
    const blob = new Blob([JSON.stringify({ ...impactState, scope: scope() }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `green-spectrum-impact-${target.dataset.impactDownload}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }
  if (target.matches("[data-impact-save-exit]")) {
    saveImpact();
    window.location.href = "../";
  }
  if (target.matches("[data-dismiss-impact-insight]")) {
    target.closest(".generated-insight").hidden = true;
  }
  if (target.matches("[data-impact-continue]")) {
    if (!document.querySelector('[name="mapReviewed"]')?.checked) {
      event.preventDefault();
      document.querySelector('[name="mapReviewed"]')?.focus();
      return;
    }
    event.preventDefault();
    const snapshot = { ...impactState, scope: scope(), savedAt: new Date().toISOString() };
    saveImpactBackend(snapshot, "completed").then(() => {
      window.location.href = target.href;
    });
  }
});

renderSignals();
renderOpportunities();
