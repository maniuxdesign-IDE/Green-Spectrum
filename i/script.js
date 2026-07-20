const progressBar = document.querySelector("#scrollProgress");

function updateScrollProgress() {
  if (!progressBar) return;
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const progress = scrollable > 0 ? window.scrollY / scrollable : 0;
  progressBar.style.width = `${Math.min(progress * 100, 100)}%`;
}

function initLandingPage() {
  const completeButtons = document.querySelectorAll("[data-complete-landing]");
  const completionState = document.querySelector("#completionState");
  if (!completeButtons.length || !completionState) return;

  function setLandingComplete(isComplete) {
    localStorage.setItem("greenSpectrumLandingComplete", isComplete ? "true" : "false");
    completionState.textContent = isComplete
      ? "Landing page completed. Page 2 is ready to design next."
      : "Landing page not completed yet";
    completeButtons.forEach((button) => {
      button.textContent = isComplete ? "Page 1 completed" : "Complete Page 1";
      button.disabled = isComplete;
    });
  }

  completeButtons.forEach((button) => {
    button.addEventListener("click", () => setLandingComplete(true));
  });

  setLandingComplete(localStorage.getItem("greenSpectrumLandingComplete") === "true");
}

function initOnboardingPage() {
  const form = document.querySelector("#onboardingForm");
  if (!form) return;

  const sections = [...document.querySelectorAll(".question-section")];
  const outputSection = document.querySelector("#journey-output");
  const onboardingState = document.querySelector("#onboardingState");
  const profileSummary = document.querySelector("#profileSummary");
  const researchSummary = document.querySelector("#researchSummary");
  const outputsSummary = document.querySelector("#outputsSummary");

  function unlockStep(step) {
    const section = document.querySelector(`[data-step="${step}"]`);
    if (!section) return;
    section.classList.remove("is-locked");
    section.classList.add("is-active");
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function markComplete(currentStep) {
    const section = document.querySelector(`[data-step="${currentStep}"]`);
    if (section) section.classList.add("is-complete");
  }

  function valuesByName(name) {
    return [...form.querySelectorAll(`[name="${name}"]:checked`)].map((input) => input.value);
  }

  function fileNames(inputName) {
    const input = form.querySelector(`[name="${inputName}"]`);
    return input?.files ? [...input.files].map((file) => file.name) : [];
  }

  function formValue(name) {
    const field = form.elements[name];
    if (!field) return "";
    if (field instanceof RadioNodeList) return field.value || "";
    return field.value || "";
  }

  function validateSection(step) {
    const section = document.querySelector(`[data-step="${step}"]`);
    const fields = [...section.querySelectorAll("input, select, textarea")];
    const requiredFields = fields.filter((field) => field.required);
    const radioGroups = new Set(
      requiredFields
        .filter((field) => field.type === "radio")
        .map((field) => field.name)
    );

    for (const field of requiredFields) {
      if (field.type === "radio") continue;
      if (!field.reportValidity()) return false;
    }

    for (const group of radioGroups) {
      if (!form.querySelector(`[name="${group}"]:checked`)) {
        form.querySelector(`[name="${group}"]`).reportValidity();
        return false;
      }
    }

    return true;
  }

  function addDefinition(list, term, value) {
    const dt = document.createElement("dt");
    dt.textContent = term;
    const dd = document.createElement("dd");
    dd.textContent = value || "Not provided";
    list.append(dt, dd);
  }

  function addListItems(list, items, fallback) {
    list.replaceChildren();
    const safeItems = items.length ? items : [fallback];
    safeItems.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      list.append(li);
    });
  }

  function buildSummary() {
    const data = {
      industry: formValue("industry"),
      mode: formValue("mode"),
      companyName: formValue("companyName"),
      companyWebsite: formValue("companyWebsite"),
      companySize: formValue("companySize"),
      companyDetails: formValue("companyDetails"),
      reportFiles: fileNames("reports"),
      reportNotes: formValue("reportNotes"),
      dataSources: valuesByName("dataSources"),
      outputs: valuesByName("outputs")
    };

    localStorage.setItem("greenSpectrumOnboarding", JSON.stringify(data));
    localStorage.setItem("greenSpectrumOnboardingComplete", "true");

    profileSummary.replaceChildren();
    addDefinition(profileSummary, "Industry", data.industry);
    addDefinition(profileSummary, "Journey mode", data.mode);
    addDefinition(profileSummary, "Company", data.companyName);
    addDefinition(profileSummary, "Website", data.companyWebsite);
    addDefinition(profileSummary, "Size", data.companySize);

    addListItems(researchSummary, [
      `Scan industry standards and regulation for ${data.industry || "the selected industry"}.`,
      `Review public signals for ${data.companyName || "the organisation"}.`,
      `Prepare risk, insurance, supply chain, and reputation prompts.`,
      ...(data.reportFiles.length
        ? [`Queue report analysis for: ${data.reportFiles.join(", ")}.`]
        : ["No uploaded report files yet. Use report notes and public sources first."]),
      ...(data.dataSources.length
        ? [`Potential integrations: ${data.dataSources.join(", ")}.`]
        : ["No operational data sources selected yet."])
    ], "No research directions yet.");

    addListItems(outputsSummary, data.outputs, "No preferred outputs selected yet.");

    outputSection.classList.remove("is-locked");
    onboardingState.textContent = "Onboarding completed. Page 3 is ready to design next.";
    outputSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  sections.forEach((section) => {
    const step = Number(section.dataset.step);
    if (step > 1) section.classList.add("is-locked");
  });

  form.querySelectorAll("[data-next-step]").forEach((button) => {
    button.addEventListener("click", () => {
      const nextStep = Number(button.dataset.nextStep);
      const currentStep = nextStep - 1;
      if (!validateSection(currentStep)) return;
      markComplete(currentStep);
      unlockStep(nextStep);
    });
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!validateSection(6)) return;
    markComplete(6);
    buildSummary();
  });
}

function initExploreMapPage() {
  const form = document.querySelector("#empathyForm");
  if (!form) return;

  const maturityLevels = [
    { key: "white", label: "White", score: 0 },
    { key: "light", label: "Light Green", score: 1 },
    { key: "mid", label: "Mid Green", score: 2 },
    { key: "dark", label: "Dark Green", score: 3 }
  ];

  const questions = [
    {
      id: "strategy-purpose",
      empathy: "Business",
      area: "Strategy and Purpose",
      keyQuestion: "Is sustainability embedded in strategic vision?",
      discovery: [
        "What are our core strategic objectives, and how do they align with sustainability imperatives?",
        "What is our current sustainability ambition or aspiration?",
        "What disruptions or opportunities are emerging in our sector due to sustainability shifts?"
      ],
      sources: "Strategy documents, annual reports, board papers, ESG benchmarking, PESTLE/STEEPV analysis, scenario planning.",
      options: {
        white: "No stated goals",
        light: "Compliance-driven mission",
        mid: "Purpose integrates across departments",
        dark: "Regenerative, mission-led, ecosystem-restoring"
      }
    },
    {
      id: "governance-leadership",
      empathy: "Business",
      area: "Governance and Leadership",
      keyQuestion: "How is sustainability governed?",
      discovery: [
        "Who owns sustainability in our organisation?",
        "What are the mindsets, values, and incentives of leadership regarding sustainability?",
        "Who are the informal influencers, champions, and resistors of change?"
      ],
      sources: "Governance charts, leadership interviews, board oversight records, power and influence matrix, organisational network analysis.",
      options: {
        white: "No governance assigned",
        light: "Board-level oversight",
        mid: "Embedded in executive performance",
        dark: "Leadership as public transformation advocates"
      }
    },
    {
      id: "culture-engagement",
      empathy: "Business",
      area: "Culture and Engagement",
      keyQuestion: "How embedded is sustainability in daily behaviour?",
      discovery: [
        "What do staff believe about sustainability and their role in it?",
        "How do people understand or misunderstand ESG?",
        "Are staff rewarded or disincentivised for initiating change?"
      ],
      sources: "Staff surveys, sensemaking interviews, change readiness assessment, behavioural insight mapping, cultural iceberg analysis.",
      options: {
        white: "No awareness",
        light: "Ad-hoc training",
        mid: "Structured engagement and champions",
        dark: "Regenerative culture and ownership"
      }
    },
    {
      id: "materiality-risk",
      empathy: "Business",
      area: "Materiality and Risk",
      keyQuestion: "How are material issues and systemic risks mapped?",
      discovery: [
        "What are the high-impact, high-risk, or high-leverage nodes?",
        "Which activities are most resource-intensive or vulnerable to disruption?",
        "What ecological, regulatory, social, or financial risks could destabilise the business?"
      ],
      sources: "Materiality mapping, ESG risk heatmaps, strategic risk radar, system maps, double materiality diagnostics.",
      options: {
        white: "No mapping",
        light: "One-time assessment",
        mid: "Dynamic system tools used",
        dark: "Full feedback loops with planetary boundaries"
      }
    },
    {
      id: "transparency-accountability",
      empathy: "Business",
      area: "Transparency and Accountability",
      keyQuestion: "How transparent is performance?",
      discovery: [
        "Are we prepared for ESG disclosures and double materiality?",
        "What data systems are needed to comply with emerging standards?",
        "How is performance communicated and verified?"
      ],
      sources: "ESG reports, ISSB/CSRD checklists, reporting dashboards, compliance audits, CDP, GRI, SBTi, B Corp evidence.",
      options: {
        white: "No disclosures",
        light: "Basic ESG reports",
        mid: "Real-time, verified metrics",
        dark: "Open data, participatory auditing"
      }
    },
    {
      id: "metrics-impact",
      empathy: "Business",
      area: "Metrics and Impact",
      keyQuestion: "Are metrics focused on impact?",
      discovery: [
        "What is currently measured?",
        "Which environmental, social, and economic impacts are invisible or unmeasured?",
        "How are metrics used in decision-making?"
      ],
      sources: "Scope 1-3 data, social impact data, biodiversity indicators, environmental profit and loss, value driver trees.",
      options: {
        white: "Only financial tracked",
        light: "Scope 1 and 2 tracked",
        mid: "Scope 3, social, biodiversity tracked",
        dark: "Regeneration, wellbeing, community wealth measured"
      }
    },
    {
      id: "product-service-innovation",
      empathy: "Business",
      area: "Product and Service Innovation",
      keyQuestion: "Are products influenced by sustainability?",
      discovery: [
        "Which revenue streams or services are at odds with sustainability goals?",
        "What financial opportunities exist in sustainable innovation?",
        "How can products or services become circular, inclusive, or regenerative?"
      ],
      sources: "Business model canvas, flourishing business canvas, opportunity portfolio mapping, circular design frameworks, design sprints.",
      options: {
        white: "Profit-focused design",
        light: "Eco-efficiency improvements",
        mid: "Circular design principles adopted",
        dark: "Products restore ecosystems and enable communities"
      }
    },
    {
      id: "operations-circularity",
      empathy: "Business",
      area: "Operations and Circularity",
      keyQuestion: "How embedded is sustainability in operations?",
      discovery: [
        "What does our current value chain look like?",
        "Which activities are most resource-intensive or vulnerable to disruption?",
        "How can we redesign parts of our value chain for resilience and sustainability?"
      ],
      sources: "Value chain mapping, supply chain flow mapping, emissions mapping, certification audits, material flow analysis.",
      options: {
        white: "Sustainability external to operations",
        light: "Certifications and audits in place",
        mid: "Circular, resilient, traceable supply chain",
        dark: "Closed-loop, zero-waste, ecosystem-restorative operations"
      }
    },
    {
      id: "finance-investment",
      empathy: "Business",
      area: "Finance and Investment",
      keyQuestion: "Are finances aligned with regeneration?",
      discovery: [
        "What is the cost of inaction on ESG issues?",
        "What ROI can we expect from sustainability-driven transformation?",
        "Where is capital reinforcing old models or enabling new ones?"
      ],
      sources: "Cash flow analysis, cost-benefit analysis, carbon pricing, green bonds, impact investment criteria, Monte Carlo risk analysis.",
      options: {
        white: "No sustainability budgets",
        light: "Green bonds or ESG screens",
        mid: "Carbon pricing and impact-first investment",
        dark: "Capital directed to ecosystem repair and social innovation"
      }
    },
    {
      id: "data-digital",
      empathy: "Business",
      area: "Data and Digital",
      keyQuestion: "How is digital tech used for sustainability?",
      discovery: [
        "What data systems are needed to comply with emerging standards?",
        "Where is data fragmented or missing?",
        "How could digital systems improve learning, traceability, or modelling?"
      ],
      sources: "ESG platforms, real-time dashboards, digital twins, AI modelling, operational data systems, data quality audits.",
      options: {
        white: "No data captured",
        light: "Basic tracking platforms",
        mid: "Integrated real-time ESG systems",
        dark: "AI, digital twins for regenerative modelling"
      }
    },
    {
      id: "policy-regulation",
      empathy: "Business",
      area: "Policy and Regulation",
      keyQuestion: "How does the organisation engage with policy?",
      discovery: [
        "What current or upcoming regulations will affect our operations?",
        "Are we prepared for ESG disclosures and double materiality?",
        "How do we engage with policy shifts beyond compliance?"
      ],
      sources: "CSRD, CBAM, ISSB and local regulatory checks, PESTLE with regulatory lens, compliance audit tools.",
      options: {
        white: "No policy awareness",
        light: "Compliance with existing frameworks",
        mid: "Strategy aligned to future policy shifts",
        dark: "Co-creation of regenerative legislation"
      }
    },
    {
      id: "collaboration-partnerships",
      empathy: "Business",
      area: "Collaboration and Partnerships",
      keyQuestion: "How strategic are sustainability partnerships?",
      discovery: [
        "Who are the critical internal and external stakeholders?",
        "What values, expectations, or needs do they hold?",
        "Where are ecosystem partnerships needed?"
      ],
      sources: "Stakeholder discovery matrix, ecosystem mapping, partnership reviews, participatory systems mapping.",
      options: {
        white: "Operates in isolation",
        light: "Member of networks",
        mid: "Strategic alliances for circular infrastructure",
        dark: "Builds coalitions for system transformation"
      }
    },
    {
      id: "innovation-rd",
      empathy: "Business",
      area: "Innovation and R&D Alignment",
      keyQuestion: "Is innovation directed to sustainability?",
      discovery: [
        "Are employees invited to contribute sustainability ideas?",
        "How is innovation managed, surfaced, or blocked internally?",
        "What cross-functional collaborations are possible?"
      ],
      sources: "Innovation readiness canvas, idea lifecycle tracking, R&D portfolio reviews, change sprint frameworks.",
      options: {
        white: "Profit-driven R&D",
        light: "Incremental sustainability innovations",
        mid: "Circular, inclusive R&D across departments",
        dark: "Regenerative, mission-led innovation"
      }
    },
    {
      id: "learning-adaptation",
      empathy: "Business",
      area: "Learning and Adaptation",
      keyQuestion: "How does the organisation learn and adapt?",
      discovery: [
        "What sustainability skills already exist across teams?",
        "What are the most urgent skill or knowledge gaps?",
        "What feedback loops help the organisation learn?"
      ],
      sources: "Green skills audit, training needs analysis, capability maturity mapping, stakeholder-role learning canvas.",
      options: {
        white: "No learning systems",
        light: "Basic sustainability training",
        mid: "Ongoing feedback loops and data tools",
        dark: "Regenerative learning cycles and reflective practice"
      }
    },
    {
      id: "crisis-resilience",
      empathy: "Business",
      area: "Crisis Readiness and Resilience",
      keyQuestion: "Is the organisation ready for disruptions?",
      discovery: [
        "How vulnerable are we to ecological shocks?",
        "What interdependent risks exist between supply chain, climate, finance, and regulation?",
        "What adaptive capacity do we have?"
      ],
      sources: "Resilience diagnostic tools, futures wheel, cross-impact analysis, polycrisis mapping, strategic foresight matrix.",
      options: {
        white: "No adaptation strategy",
        light: "Contingency plans for known risks",
        mid: "Stress testing and adaptive planning",
        dark: "Antifragility and distributed systems thrive in uncertainty"
      }
    },
    {
      id: "regenerative-identity",
      empathy: "Business",
      area: "Regenerative Business Identity",
      keyQuestion: "Is the business redefining its role in a planetary emergency?",
      discovery: [
        "How would a regenerative strategy shift our market position?",
        "Can our operations regenerate ecosystems or resources?",
        "Where can we shift from harm reduction to value creation?"
      ],
      sources: "Regenerative business maturity framework, net-positive business design, backcasting from regenerative futures.",
      options: {
        white: "Profit-maximising actor",
        light: "Risk-driven sustainability response",
        mid: "Purpose-led exemplar for circular economy",
        dark: "Movement partner, moral actor, ecological trustee"
      }
    },
    {
      id: "ecosystem-stewardship",
      empathy: "Planetary",
      area: "Ecosystem Stewardship",
      keyQuestion: "Is ecological regeneration supported?",
      discovery: [
        "Which planetary systems do we most affect or depend on?",
        "Where can we shift from harm reduction to value creation for nature?",
        "Can operations regenerate ecosystems or resources?"
      ],
      sources: "Ecosystem services mapping, biodiversity assessments, nature-based solutions portfolio, place-based stewardship evidence.",
      options: {
        white: "No involvement",
        light: "Offsets or biodiversity pledges",
        mid: "Active regeneration projects",
        dark: "Place-based stewardship and infrastructure investment"
      }
    },
    {
      id: "value-chain-traceability",
      empathy: "Planetary",
      area: "Value Chain and Traceability",
      keyQuestion: "How aligned and traceable are partners?",
      discovery: [
        "What does our current value chain look like?",
        "Where are high-impact, high-risk, or high-leverage nodes?",
        "Which supplier relationships influence ecological and social outcomes?"
      ],
      sources: "Supply chain audits, traceability platforms, supplier codes, emissions mapping, participatory systems mapping.",
      options: {
        white: "Focus on cost and delivery",
        light: "Supplier codes and audits",
        mid: "Full traceability across supply chain",
        dark: "Co-governance with regenerative suppliers"
      }
    },
    {
      id: "circular-design-materials",
      empathy: "Planetary",
      area: "Circular Design and Materials",
      keyQuestion: "Are materials and design circular?",
      discovery: [
        "What raw materials do we depend on?",
        "Are these sustainable, ethical, circular, or finite?",
        "How much waste do we create, and where does it go?"
      ],
      sources: "Material flow analysis, circularity opportunity mapping, cradle to cradle design, circular value chain canvas.",
      options: {
        white: "No guidance or lifecycle thinking",
        light: "Single-attribute improvements",
        mid: "Circularity design frameworks used",
        dark: "Biomimicry and net-positive materials applied"
      }
    },
    {
      id: "climate-biodiversity",
      empathy: "Planetary",
      area: "Climate and Biodiversity Integration",
      keyQuestion: "How embedded are climate and nature in decisions?",
      discovery: [
        "What is the full lifecycle impact of our products or services?",
        "Where are the highest emissions, waste, or pollution outputs?",
        "Are we operating within planetary boundaries?"
      ],
      sources: "Lifecycle assessment, Scope 1-3 carbon accounting, planetary boundaries, doughnut economics, environmental impact maps.",
      options: {
        white: "No consideration",
        light: "Carbon reporting and disclosure",
        mid: "Science-based targets and nature-positive principles",
        dark: "Regenerative action drives investment"
      }
    },
    {
      id: "stakeholder-engagement",
      empathy: "Human",
      area: "Stakeholder Engagement",
      keyQuestion: "How are stakeholders shaping the agenda?",
      discovery: [
        "Who are the critical stakeholders?",
        "What values, expectations, or needs do they hold?",
        "Where are there blind spots in stakeholder representation?"
      ],
      sources: "Stakeholder discovery matrix, empathy mapping, personas, stakeholder journey maps, inclusion gap analysis.",
      options: {
        white: "Passive recipients",
        light: "Surveys and reports",
        mid: "Regular co-creation sessions",
        dark: "Long-term participatory governance"
      }
    },
    {
      id: "behaviour-change",
      empathy: "Human",
      area: "Behavioural Change and Incentives",
      keyQuestion: "How are employees enabled to act?",
      discovery: [
        "What emotional barriers such as apathy, fear, or distrust exist?",
        "Are staff rewarded or disincentivised for initiating change?",
        "What role-specific support is needed?"
      ],
      sources: "Behavioural insight mapping, change readiness assessment, staff surveys, leadership alignment interviews.",
      options: {
        white: "No connection to roles or performance",
        light: "Basic training offered",
        mid: "Sustainability linked to performance",
        dark: "Regenerative leadership and peer learning embedded"
      }
    },
    {
      id: "customer-engagement",
      empathy: "Human",
      area: "Customer Engagement",
      keyQuestion: "How are customers empowered?",
      discovery: [
        "How do customers experience the sustainability challenge?",
        "Where are claims, choices, or behaviours confusing?",
        "How could customers participate in regenerative solutions?"
      ],
      sources: "Customer research, journey maps, decision-making tools, co-design workshops, communication audits.",
      options: {
        white: "No sustainability communication",
        light: "Product badges or claims",
        mid: "Education and decision-making tools provided",
        dark: "Co-creation of regenerative solutions with customers"
      }
    },
    {
      id: "wellbeing-community",
      empathy: "Human",
      area: "Human and Community Wellbeing",
      keyQuestion: "How is wellbeing supported internally and externally?",
      discovery: [
        "What do people experience in relation to this challenge?",
        "What harms, frustrations, or inequities are repeated?",
        "Which communities are affected by decisions?"
      ],
      sources: "Wellbeing assessments, CSR evidence, community interviews, equity assessments, social impact data.",
      options: {
        white: "No wellbeing or equity focus",
        light: "Standard benefits and CSR efforts",
        mid: "Living wages and equity assessments",
        dark: "Long-term partnerships regenerate communities"
      }
    },
    {
      id: "equity-justice-inclusion",
      empathy: "Human",
      area: "Equity, Justice and Inclusion",
      keyQuestion: "How is justice embedded in efforts?",
      discovery: [
        "Where are there blind spots in stakeholder representation?",
        "Whose needs, labour, risks, or knowledge are overlooked?",
        "How could affected people co-lead systems change?"
      ],
      sources: "Inclusion gap analysis, justice procurement reviews, participatory systems mapping, anti-oppressive design methods.",
      options: {
        white: "No DEI considerations",
        light: "Diversity pledges or training",
        mid: "Equity-centred design and justice procurement",
        dark: "Anti-oppressive, intersectional systems change co-led"
      }
    }
  ];

  const containers = {
    Business: document.querySelector("#businessQuestions"),
    Planetary: document.querySelector("#planetaryQuestions"),
    Human: document.querySelector("#humanQuestions")
  };
  const sectionByEmpathy = {
    Business: document.querySelector('[data-empathy="Business"]'),
    Planetary: document.querySelector('[data-empathy="Planetary"]'),
    Human: document.querySelector('[data-empathy="Human"]')
  };

  function renderQuestion(question, index) {
    const card = document.createElement("article");
    card.className = "empathy-question-card";
    card.dataset.question = question.id;
    const optionMarkup = maturityLevels.map((level) => `
      <label class="maturity-option ${level.key}">
        <input type="radio" name="${question.id}" value="${level.score}" required>
        <span>${level.label}</span>
        <small>${question.options[level.key]}</small>
      </label>
    `).join("");

    card.innerHTML = `
      <div class="question-index">${String(index + 1).padStart(2, "0")}</div>
      <div class="question-body">
        <p class="eyebrow">${question.empathy} / ${question.area}</p>
        <h3>${question.keyQuestion}</h3>
        <details>
          <summary>Discovery prompts and where to find the information</summary>
          <ul>${question.discovery.map((item) => `<li>${item}</li>`).join("")}</ul>
          <p><strong>Sources and tools:</strong> ${question.sources}</p>
        </details>
        <fieldset class="maturity-options">
          <legend>Select the current maturity level</legend>
          ${optionMarkup}
        </fieldset>
      </div>
    `;
    return card;
  }

  Object.keys(containers).forEach((empathy) => {
    questions
      .filter((question) => question.empathy === empathy)
      .forEach((question, index) => containers[empathy].append(renderQuestion(question, index)));
  });

  function empathyQuestions(empathy) {
    return questions.filter((question) => question.empathy === empathy);
  }

  function validateEmpathy(empathy) {
    const missing = empathyQuestions(empathy).find((question) => !form.querySelector(`[name="${question.id}"]:checked`));
    if (!missing) return true;
    const card = form.querySelector(`[data-question="${missing.id}"]`);
    card.scrollIntoView({ behavior: "smooth", block: "center" });
    card.classList.add("needs-answer");
    setTimeout(() => card.classList.remove("needs-answer"), 1200);
    return false;
  }

  function unlockEmpathy(empathy) {
    const section = sectionByEmpathy[empathy];
    if (!section) return;
    section.classList.remove("is-locked");
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function selectedScore(question) {
    const selected = form.querySelector(`[name="${question.id}"]:checked`);
    return selected ? Number(selected.value) : 0;
  }

  function labelForAverage(score) {
    if (score < 0.75) return "White";
    if (score < 1.5) return "Light Green";
    if (score < 2.35) return "Mid Green";
    return "Dark Green";
  }

  function cynefinForScore(score) {
    if (score <= 0.75) return "Chaotic: stabilise first, create visibility, gather evidence, and establish ownership.";
    if (score <= 1.5) return "Complicated: diagnose with experts, benchmark, and build a targeted improvement roadmap.";
    if (score <= 2.35) return "Complex: use co-creation, systems mapping, experiments, and adaptive learning loops.";
    return "Clear/Enabling: scale what works, share practice, and use the organisation as a platform for wider system change.";
  }

  function addDefinition(list, term, value) {
    const dt = document.createElement("dt");
    dt.textContent = term;
    const dd = document.createElement("dd");
    dd.textContent = value;
    list.append(dt, dd);
  }

  function buildExploreOutput() {
    const maturitySummary = document.querySelector("#maturitySummary");
    const hotspotSummary = document.querySelector("#hotspotSummary");
    const cynefinSummary = document.querySelector("#cynefinSummary");
    const outputSection = document.querySelector("#explore-output");
    const exploreState = document.querySelector("#exploreState");

    const answered = questions.map((question) => ({
      ...question,
      score: selectedScore(question)
    }));
    const byEmpathy = ["Business", "Planetary", "Human"].map((empathy) => {
      const items = answered.filter((item) => item.empathy === empathy);
      const average = items.reduce((sum, item) => sum + item.score, 0) / items.length;
      return { empathy, average, label: labelForAverage(average), items };
    });
    const hotspots = answered
      .filter((item) => item.score <= 1)
      .sort((a, b) => a.score - b.score)
      .slice(0, 8);
    const clusters = byEmpathy
      .map((group) => `${group.empathy}: ${group.items.filter((item) => item.score <= 1).length} low-maturity hotspots`)
      .filter(Boolean);

    maturitySummary.replaceChildren();
    byEmpathy.forEach((group) => {
      addDefinition(maturitySummary, group.empathy, `${group.label} (${group.average.toFixed(1)} / 3)`);
    });

    hotspotSummary.replaceChildren();
    (hotspots.length ? hotspots : answered.slice(0, 3)).forEach((item) => {
      const li = document.createElement("li");
      li.textContent = `${item.area}: ${maturityLevels[item.score].label}. ${item.keyQuestion}`;
      hotspotSummary.append(li);
    });
    clusters.forEach((cluster) => {
      const li = document.createElement("li");
      li.textContent = cluster;
      hotspotSummary.append(li);
    });

    cynefinSummary.replaceChildren();
    byEmpathy.forEach((group) => {
      const li = document.createElement("li");
      li.textContent = `${group.empathy}: ${cynefinForScore(group.average)}`;
      cynefinSummary.append(li);
    });

    localStorage.setItem("greenSpectrumExploreMap", JSON.stringify({ byEmpathy, hotspots }));
    localStorage.setItem("greenSpectrumExploreMapComplete", "true");
    outputSection.classList.remove("is-locked");
    exploreState.textContent = "Explore and Map completed. Page 4 is ready to design next.";
    outputSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  form.querySelectorAll("[data-complete-empathy]").forEach((button) => {
    button.addEventListener("click", () => {
      const empathy = button.dataset.completeEmpathy;
      if (!validateEmpathy(empathy)) return;
      sectionByEmpathy[empathy].classList.add("is-complete");
      unlockEmpathy(button.dataset.nextEmpathy);
    });
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!validateEmpathy("Human")) return;
    sectionByEmpathy.Human.classList.add("is-complete");
    buildExploreOutput();
  });
}

function initImpactJourneyPage() {
  const form = document.querySelector("#impactJourneyForm");
  if (!form) return;

  const stageBuilder = document.querySelector("#stageBuilder");
  const journeyBoard = document.querySelector("#journeyBoard");
  const outputSection = document.querySelector("#impact-output");
  const impactState = document.querySelector("#impactState");
  const stageDefaults = ["Inputs", "Production", "Distribution", "Use", "End of life"];
  const canvasRows = [
    {
      key: "stakeholders",
      label: "Stakeholders involved",
      prompt: "Teams, suppliers, customers, regulators, communities, partners."
    },
    {
      key: "activities",
      label: "Key activities",
      prompt: "Main tasks, functions, handoffs, operational steps, decisions."
    },
    {
      key: "assumptions",
      label: "Assumptions and unknowns",
      prompt: "Missing evidence, guesses, uncertainties, risks, data gaps."
    },
    {
      key: "interdependencies",
      label: "Interdependencies and system interactions",
      prompt: "Dependencies, feedback loops, upstream/downstream effects."
    },
    {
      key: "experience",
      label: "User emotions and experience",
      prompt: "Friction, trust, confusion, pressure, effort, behaviour."
    },
    {
      key: "environmental",
      label: "Environmental impact",
      prompt: "Carbon, energy, water, materials, waste, biodiversity, pollution."
    },
    {
      key: "social",
      label: "Social impact",
      prompt: "Labour, health, equity, community, access, wellbeing."
    },
    {
      key: "governance",
      label: "Governance impact",
      prompt: "Compliance, accountability, disclosure, ownership, decision rights."
    }
  ];

  function renderStageBuilder() {
    stageBuilder.replaceChildren();
    stageDefaults.forEach((stage, index) => {
      const label = document.createElement("label");
      label.className = "stage-name-card";
      label.innerHTML = `
        <span>Stage ${index + 1}</span>
        <input type="text" name="stage-${index}" value="${stage}" required>
      `;
      stageBuilder.append(label);
    });
  }

  function stageNames() {
    return stageDefaults.map((_, index) => form.elements[`stage-${index}`]?.value.trim() || `Stage ${index + 1}`);
  }

  function unlockJourneyStep(step) {
    const section = document.querySelector(`[data-journey-step="${step}"]`);
    if (!section) return;
    section.classList.remove("is-locked");
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function completeJourneyStep(step) {
    const section = document.querySelector(`[data-journey-step="${step}"]`);
    if (section) section.classList.add("is-complete");
  }

  function renderJourneyBoard() {
    const stages = stageNames();
    journeyBoard.replaceChildren();
    journeyBoard.style.setProperty("--stage-count", stages.length);

    const corner = document.createElement("div");
    corner.className = "journey-cell journey-corner";
    corner.textContent = "Stage / phase";
    journeyBoard.append(corner);

    stages.forEach((stage, index) => {
      const cell = document.createElement("div");
      cell.className = "journey-cell journey-stage";
      cell.innerHTML = `<span>Stage ${index + 1}</span><strong>${stage}</strong>`;
      journeyBoard.append(cell);
    });

    canvasRows.forEach((row) => {
      const rowLabel = document.createElement("div");
      rowLabel.className = "journey-cell journey-row-label";
      rowLabel.innerHTML = `<strong>${row.label}</strong><small>${row.prompt}</small>`;
      journeyBoard.append(rowLabel);

      stages.forEach((stage, index) => {
        const field = document.createElement("label");
        field.className = "journey-cell journey-entry";
        field.innerHTML = `
          <span>${stage}</span>
          <textarea name="${row.key}-${index}" rows="4" placeholder="${row.prompt}"></textarea>
        `;
        journeyBoard.append(field);
      });
    });
  }

  function textValue(name) {
    return form.elements[name]?.value.trim() || "";
  }

  function collectJourneyData() {
    const stages = stageNames();
    return stages.map((stage, stageIndex) => {
      const values = {};
      canvasRows.forEach((row) => {
        values[row.key] = textValue(`${row.key}-${stageIndex}`);
      });
      return { stage, values };
    });
  }

  function countImpactSignals(stage) {
    return ["environmental", "social", "governance"].reduce((count, key) => {
      return count + (stage.values[key] ? 1 : 0);
    }, 0);
  }

  function appendItems(list, items, fallback) {
    list.replaceChildren();
    (items.length ? items : [fallback]).forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      list.append(li);
    });
  }

  function addDefinition(list, term, value) {
    const dt = document.createElement("dt");
    dt.textContent = term;
    const dd = document.createElement("dd");
    dd.textContent = value || "Not provided yet";
    list.append(dt, dd);
  }

  function buildImpactOutput() {
    const journey = collectJourneyData();
    const priorityStageSummary = document.querySelector("#priorityStageSummary");
    const impactClusterSummary = document.querySelector("#impactClusterSummary");
    const dataNeedSummary = document.querySelector("#dataNeedSummary");
    const narrativeSummary = document.querySelector("#journeyNarrativeSummary");
    const rankedStages = [...journey]
      .map((stage) => ({
        ...stage,
        impactSignals: countImpactSignals(stage),
        unknowns: stage.values.assumptions ? 1 : 0,
        interdependencies: stage.values.interdependencies ? 1 : 0
      }))
      .sort((a, b) => {
        return (b.impactSignals + b.unknowns + b.interdependencies) - (a.impactSignals + a.unknowns + a.interdependencies);
      });

    appendItems(
      priorityStageSummary,
      rankedStages.slice(0, 3).map((stage) => {
        return `${stage.stage}: ${stage.impactSignals} ESG impact areas mapped, ${stage.unknowns ? "unknowns present" : "few unknowns"}, ${stage.interdependencies ? "system interactions present" : "limited system interactions"}.`;
      }),
      "No priority stages mapped yet."
    );

    const clusters = [];
    ["environmental", "social", "governance"].forEach((key) => {
      const row = canvasRows.find((item) => item.key === key);
      const stages = journey.filter((stage) => stage.values[key]).map((stage) => stage.stage);
      if (stages.length) clusters.push(`${row.label}: mapped across ${stages.join(", ")}.`);
    });
    appendItems(impactClusterSummary, clusters, "No impact clusters mapped yet.");

    const needs = [];
    journey.forEach((stage) => {
      if (stage.values.assumptions) needs.push(`${stage.stage}: validate assumptions and unknowns.`);
      if (stage.values.interdependencies) needs.push(`${stage.stage}: investigate system interactions and dependencies.`);
      if (stage.values.activities && !stage.values.environmental) needs.push(`${stage.stage}: add environmental impact evidence.`);
      if (stage.values.activities && !stage.values.social) needs.push(`${stage.stage}: add social impact evidence.`);
      if (stage.values.activities && !stage.values.governance) needs.push(`${stage.stage}: add governance impact evidence.`);
    });
    appendItems(dataNeedSummary, needs.slice(0, 8), "No data needs identified yet.");

    narrativeSummary.replaceChildren();
    addDefinition(narrativeSummary, "Potential opportunities", textValue("opportunities"));
    addDefinition(narrativeSummary, "Analysis", textValue("analysis"));
    addDefinition(narrativeSummary, "Results", textValue("results"));

    localStorage.setItem("greenSpectrumImpactJourney", JSON.stringify({
      journey,
      opportunities: textValue("opportunities"),
      analysis: textValue("analysis"),
      results: textValue("results")
    }));
    localStorage.setItem("greenSpectrumImpactJourneyComplete", "true");
    outputSection.classList.remove("is-locked");
    impactState.textContent = "Impact Journey Mapping completed. Page 5 is ready to design next.";
    outputSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  form.querySelectorAll("[data-complete-journey-step]").forEach((button) => {
    button.addEventListener("click", () => {
      const current = Number(button.dataset.completeJourneyStep);
      const next = Number(button.dataset.nextJourneyStep);
      if (current === 1) {
        const invalid = stageDefaults.some((_, index) => !form.elements[`stage-${index}`].reportValidity());
        if (invalid) return;
        renderJourneyBoard();
      }
      completeJourneyStep(current);
      unlockJourneyStep(next);
    });
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    completeJourneyStep(3);
    buildImpactOutput();
  });

  renderStageBuilder();
}

function initSortPrioritisePage() {
  const form = document.querySelector("#sortPrioritiseForm");
  if (!form) return;

  const cardList = document.querySelector("#problemCardList");
  const addButton = document.querySelector("#addProblemButton");
  const sortButton = document.querySelector("#sortProblemsButton");
  const decisionButton = document.querySelector("#buildDecisionTreesButton");
  const visualSection = document.querySelector("#visual-priority-map");
  const decisionSection = document.querySelector("#decision-tree-section");
  const outputSection = document.querySelector("#sort-output");
  const sortState = document.querySelector("#sortState");
  let problems = [];
  let selectedProblemIds = [];

  const spectrum = {
    light: {
      label: "Light Green",
      focus: "Compliance, less harm, alignment, education, foundations, transparency.",
      method: "Checklists, standards, reporting templates, simple controls.",
      outcome: "A defensible ESG foundation with named owners, evidence, review cycles, and corrective actions."
    },
    mid: {
      label: "Mid Green",
      focus: "Sustainable or circular systemic change across business model, value chain, and stakeholders.",
      method: "Capability assessment, circular design, LCA, business architecture, structured pilots.",
      outcome: "A more resilient operating model with shared KPIs, redesigned flows, and learning loops."
    },
    dark: {
      label: "Dark Green",
      focus: "Regenerative, nature-based transformation across business, planet, people, and long-range value.",
      method: "Systems mapping, foresight, co-creation, policy design, regenerative governance.",
      outcome: "A regenerative direction with new measures, new narratives, and ecosystem-level intervention logic."
    }
  };

  const cynefin = {
    simple: {
      label: "Simple",
      action: "Use a known practice.",
      method: "Sense, categorise, respond with a checklist or standard operating process."
    },
    complicated: {
      label: "Complicated",
      action: "Bring in expert analysis.",
      method: "Diagnose, compare frameworks, model options, assign owners, and build an evidence pack."
    },
    complex: {
      label: "Complex",
      action: "Learn through doing.",
      method: "Probe, sense, respond with prototypes, stakeholder loops, and adaptive decision making."
    },
    chaotic: {
      label: "Chaotic",
      action: "Stabilise first.",
      method: "Contain harm, preserve evidence, communicate carefully, then reassess the root cause."
    },
    confused: {
      label: "Confused",
      action: "Run discovery.",
      method: "Clarify ownership, language, data, business reason, and which domain the issue belongs to."
    }
  };

  const domainMethods = {
    reporting: "GRI, ESRS, ISSB, IFRS S1/S2, GHG Protocol, evidence hierarchy.",
    data: "ESG data governance, metric dictionary, source register, audit trail.",
    behaviour: "COM-B diagnosis, EAST checklist, role-based learning, change experiments.",
    supply: "GHG Scope 3, supplier segmentation, ISO 20400, procurement clauses.",
    product: "Circular Design Guide, LCA, Design for X, material circularity.",
    material: "Safe and Sustainable by Design, LCA, Cradle to Cradle, material passports.",
    business: "Sustainable Business Model Canvas, Flourishing Business Canvas, Three Horizons.",
    governance: "RACI, ISSB governance pillar, ISO 14001, operating model design.",
    systems: "Systems mapping, Meadows leverage points, Theory of Change, systemic design.",
    risk: "Materiality, ISO 31000, scenario analysis, climate and transition risk."
  };

  const examplesByRoute = {
    "light-simple": ["Track Scope 1 and 2 emissions", "Assign ESG data roles", "Use standard ESG templates", "Run basic waste tracking"],
    "light-complicated": ["Select ESG frameworks", "Build an emissions baseline", "Run supplier ESG assessment", "Perform energy or waste audit"],
    "light-complex": ["Coordinate cross-department data", "Engage suppliers for Scope 3", "Address green fatigue", "Translate policy into behaviour"],
    "light-chaotic": ["Contain greenwashing fallout", "Respond to utility disruption", "Fix legal waste breach", "Stabilise urgent ESG risk"],
    "light-confused": ["Appoint a temporary ESG owner", "Create data inventory", "Run materiality scan", "Build supplier visibility"],
    "mid-simple": ["Assign sustainability roles", "Set departmental responsibilities", "Add ESG KPIs", "Pilot obvious upgrades"],
    "mid-complicated": ["Create ESG dashboard", "Model circular business case", "Source low-impact materials", "Negotiate partner targets"],
    "mid-complex": ["Redesign operations", "Resolve department conflicts", "Design reverse logistics", "Co-develop shared infrastructure"],
    "mid-chaotic": ["Respond to supply collapse", "Meet major customer ESG demand", "Resolve strategy contradiction", "Run executive intervention"],
    "mid-confused": ["Create shared language", "Run materiality workshop", "Set vision and priorities", "Build roadmap"],
    "dark-simple": ["Commit to net-positive goal", "Include non-human stakeholders", "Add long-term roles", "Update regenerative purpose"],
    "dark-complicated": ["Create biodiversity metrics", "Build regenerative market fit", "Run long-range scenario planning", "Align new narratives"],
    "dark-complex": ["Define new value systems", "Host participatory futures work", "Design for long feedback loops", "Build uncertainty governance"],
    "dark-chaotic": ["Navigate industry collapse", "Handle transformation trust rupture", "Absorb ecological disruption", "Protect capacity under extreme pivot"],
    "dark-confused": ["Resolve identity conflict", "Reconcile competing futures", "Rebuild governance for regeneration", "Clarify strategic ethics"]
  };

  function previousPageSeeds() {
    const seeds = [];
    try {
      const impact = JSON.parse(localStorage.getItem("greenSpectrumImpactJourney") || "{}");
      if (impact.results) seeds.push({ title: "Impact journey result hotspot", evidence: impact.results });
      if (impact.opportunities) seeds.push({ title: "Mapped opportunity from the journey", evidence: impact.opportunities });
      if (Array.isArray(impact.journey)) {
        impact.journey.slice(0, 3).forEach((stage) => {
          const impacts = ["environmental", "social", "governance"]
            .filter((key) => stage.values?.[key])
            .map((key) => `${key}: ${stage.values[key]}`)
            .join("; ");
          if (impacts) seeds.push({ title: `${stage.stage} impact cluster`, evidence: impacts });
        });
      }
    } catch (error) {
      seeds.length = 0;
    }
    return seeds.slice(0, 5);
  }

  function defaultProblems() {
    const seeds = previousPageSeeds();
    const fallback = [
      { title: "Fragmented supplier emissions data", evidence: "Scope 3 information is incomplete, inconsistent, or hard to verify.", domain: "supply", spectrum: "light", cynefin: "complex", impact: 4, effort: 3, strategic: 4, urgency: 3, confidence: 2 },
      { title: "Packaging waste across the value chain", evidence: "Materials, procurement, customer use, and end-of-life impacts need clearer redesign options.", domain: "product", spectrum: "mid", cynefin: "complicated", impact: 4, effort: 3, strategic: 4, urgency: 3, confidence: 3 },
      { title: "Unclear ESG ownership and reporting", evidence: "No single owner, data dictionary, review cadence, or evidence folder exists.", domain: "governance", spectrum: "light", cynefin: "confused", impact: 3, effort: 2, strategic: 4, urgency: 4, confidence: 3 },
      { title: "High logistics energy use", evidence: "Transport routes, fuel data, supplier choices, and customer commitments suggest an emissions hotspot.", domain: "data", spectrum: "mid", cynefin: "complicated", impact: 5, effort: 3, strategic: 4, urgency: 3, confidence: 3 },
      { title: "Low stakeholder participation in sustainability decisions", evidence: "Affected teams, suppliers, customers, or communities are not shaping decisions early enough.", domain: "systems", spectrum: "dark", cynefin: "complex", impact: 4, effort: 4, strategic: 5, urgency: 3, confidence: 2 }
    ];
    return (seeds.length ? seeds : fallback).map((seed, index) => ({
      id: `problem-${Date.now()}-${index}`,
      title: seed.title,
      evidence: seed.evidence || "",
      domain: seed.domain || "systems",
      spectrum: seed.spectrum || (index % 3 === 0 ? "light" : index % 3 === 1 ? "mid" : "dark"),
      cynefin: seed.cynefin || (index % 2 === 0 ? "complex" : "complicated"),
      impact: seed.impact || 4,
      effort: seed.effort || 3,
      strategic: seed.strategic || 4,
      urgency: seed.urgency || 3,
      confidence: seed.confidence || 2,
      reflection: ""
    }));
  }

  function createOption(value, label, selected) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    option.selected = value === selected;
    return option;
  }

  function createRangeLabel(name, value) {
    const label = document.createElement("label");
    label.textContent = name;
    const input = document.createElement("input");
    input.type = "range";
    input.min = "1";
    input.max = "5";
    input.value = String(value);
    input.dataset.field = name.toLowerCase();
    const small = document.createElement("small");
    small.textContent = `${value} / 5`;
    input.addEventListener("input", () => {
      small.textContent = `${input.value} / 5`;
    });
    label.append(input, small);
    return label;
  }

  function renderProblemCards() {
    cardList.replaceChildren();
    problems.forEach((problem, index) => {
      const card = document.createElement("article");
      card.className = "problem-card";
      card.dataset.problemId = problem.id;

      const header = document.createElement("div");
      header.className = "problem-card-header";
      const number = document.createElement("span");
      number.className = "problem-number";
      number.textContent = String(index + 1).padStart(2, "0");
      const copy = document.createElement("div");
      copy.innerHTML = `<h3>Problem signal</h3><p>Define the challenge, then classify it using the Green Spectrum and Cynefin routing questions.</p>`;
      header.append(number, copy);

      const mainFields = document.createElement("div");
      mainFields.className = "problem-main-fields";
      const titleLabel = document.createElement("label");
      titleLabel.textContent = "Problem title";
      const titleInput = document.createElement("input");
      titleInput.type = "text";
      titleInput.dataset.field = "title";
      titleInput.required = true;
      titleInput.value = problem.title;
      titleLabel.append(titleInput);
      const evidenceLabel = document.createElement("label");
      evidenceLabel.textContent = "Evidence or source";
      const evidenceInput = document.createElement("textarea");
      evidenceInput.rows = 4;
      evidenceInput.dataset.field = "evidence";
      evidenceInput.placeholder = "Reports, journey map insight, stakeholder quote, data source, public signal, or assumption.";
      evidenceInput.value = problem.evidence;
      evidenceLabel.append(evidenceInput);
      mainFields.append(titleLabel, evidenceLabel);

      const ratingGrid = document.createElement("div");
      ratingGrid.className = "problem-rating-grid";
      ratingGrid.append(
        createRangeLabel("Impact", problem.impact),
        createRangeLabel("Effort", problem.effort),
        createRangeLabel("Strategic", problem.strategic),
        createRangeLabel("Urgency", problem.urgency)
      );

      const classify = document.createElement("div");
      classify.className = "classification-grid";
      const domainLabel = document.createElement("label");
      domainLabel.textContent = "Problem domain";
      const domainSelect = document.createElement("select");
      domainSelect.dataset.field = "domain";
      Object.keys(domainMethods).forEach((key) => domainSelect.append(createOption(key, key[0].toUpperCase() + key.slice(1), problem.domain)));
      domainLabel.append(domainSelect, document.createElement("small"));
      domainLabel.querySelector("small").textContent = "What discipline or evidence base should the backend route toward?";

      const spectrumLabel = document.createElement("label");
      spectrumLabel.textContent = "Green Spectrum maturity";
      const spectrumSelect = document.createElement("select");
      spectrumSelect.dataset.field = "spectrum";
      Object.entries(spectrum).forEach(([key, item]) => spectrumSelect.append(createOption(key, item.label, problem.spectrum)));
      spectrumLabel.append(spectrumSelect, document.createElement("small"));
      spectrumLabel.querySelector("small").textContent = "Harm reduction, systemic change, or regenerative transformation.";

      const cynefinLabel = document.createElement("label");
      cynefinLabel.textContent = "Cynefin complexity";
      const cynefinSelect = document.createElement("select");
      cynefinSelect.dataset.field = "cynefin";
      Object.entries(cynefin).forEach(([key, item]) => cynefinSelect.append(createOption(key, item.label, problem.cynefin)));
      cynefinLabel.append(cynefinSelect, document.createElement("small"));
      cynefinLabel.querySelector("small").textContent = "Known solution, expert analysis, experiment, crisis, or unclear domain.";

      const confidenceLabel = document.createElement("label");
      confidenceLabel.textContent = "Evidence confidence";
      const confidenceInput = document.createElement("input");
      confidenceInput.type = "range";
      confidenceInput.min = "1";
      confidenceInput.max = "5";
      confidenceInput.value = String(problem.confidence);
      confidenceInput.dataset.field = "confidence";
      const confidenceSmall = document.createElement("small");
      confidenceSmall.textContent = `${problem.confidence} / 5. Low confidence should trigger more discovery before prototyping.`;
      confidenceInput.addEventListener("input", () => {
        confidenceSmall.textContent = `${confidenceInput.value} / 5. Low confidence should trigger more discovery before prototyping.`;
      });
      confidenceLabel.append(confidenceInput, confidenceSmall);
      classify.append(domainLabel, spectrumLabel, cynefinLabel, confidenceLabel);

      const reflection = document.createElement("div");
      reflection.className = "reflection-grid";
      const reflectLabel = document.createElement("label");
      reflectLabel.textContent = "Team reflection";
      const reflectInput = document.createElement("textarea");
      reflectInput.rows = 3;
      reflectInput.dataset.field = "reflection";
      reflectInput.placeholder = "Where is the disagreement, uncertainty, or missing system map?";
      reflectInput.value = problem.reflection || "";
      reflectLabel.append(reflectInput);
      reflection.append(reflectLabel);

      card.append(header, mainFields, ratingGrid, classify, reflection);
      cardList.append(card);
    });
  }

  function collectProblems() {
    problems = [...cardList.querySelectorAll(".problem-card")].map((card) => {
      const field = (name) => card.querySelector(`[data-field="${name}"]`);
      return {
        id: card.dataset.problemId,
        title: field("title").value.trim(),
        evidence: field("evidence").value.trim(),
        domain: field("domain").value,
        spectrum: field("spectrum").value,
        cynefin: field("cynefin").value,
        impact: Number(field("impact").value),
        effort: Number(field("effort").value),
        strategic: Number(field("strategic").value),
        urgency: Number(field("urgency").value),
        confidence: Number(field("confidence").value),
        reflection: field("reflection").value.trim()
      };
    }).filter((problem) => problem.title);
    localStorage.setItem("greenSpectrumSortProblems", JSON.stringify(problems));
    return problems;
  }

  function score(problem) {
    return (problem.impact * 2) + (problem.strategic * 2) + problem.urgency + problem.confidence - problem.effort;
  }

  function tagsFor(problem) {
    const tags = [`${spectrum[problem.spectrum].label}`, `${cynefin[problem.cynefin].label}`, problem.domain];
    if (problem.impact >= 4 && problem.effort <= 2) tags.push("low hanging fruit");
    if (problem.strategic >= 4) tags.push("strategic");
    if (problem.confidence <= 2) tags.push("more discovery");
    return tags;
  }

  function chip(problem) {
    const span = document.createElement("span");
    span.className = `problem-chip ${problem.spectrum}`;
    span.textContent = problem.title;
    return span;
  }

  function renderHeatmap() {
    const grid = document.querySelector("#heatmapGrid");
    grid.replaceChildren();
    for (let impact = 5; impact >= 1; impact -= 1) {
      for (let effort = 1; effort <= 5; effort += 1) {
        const cell = document.createElement("div");
        cell.className = "heatmap-cell";
        if (impact >= 4 && effort <= 2) cell.classList.add("is-prime");
        const coord = document.createElement("span");
        coord.className = "cell-coord";
        coord.textContent = `I${impact} / E${effort}`;
        cell.append(coord);
        problems.filter((problem) => problem.impact === impact && problem.effort === effort).forEach((problem) => {
          cell.append(chip(problem));
        });
        grid.append(cell);
      }
    }
  }

  function renderSpectrumLanes() {
    const lanes = document.querySelector("#spectrumLanes");
    lanes.replaceChildren();
    Object.entries(spectrum).forEach(([key, item]) => {
      const lane = document.createElement("section");
      lane.className = "spectrum-lane";
      const header = document.createElement("header");
      header.innerHTML = `<h4>${item.label}</h4><p>${item.focus}</p>`;
      lane.append(header);
      problems.filter((problem) => problem.spectrum === key).forEach((problem) => lane.append(chip(problem)));
      lanes.append(lane);
    });
  }

  function renderCynefinBoard() {
    const board = document.querySelector("#cynefinBoard");
    board.replaceChildren();
    ["complex", "complicated", "chaotic", "simple", "confused"].forEach((key) => {
      const quadrant = document.createElement("section");
      quadrant.className = `cynefin-quadrant ${key}`;
      quadrant.innerHTML = `<h4>${cynefin[key].label}</h4><p>${cynefin[key].action}</p>`;
      problems.filter((problem) => problem.cynefin === key).forEach((problem) => quadrant.append(chip(problem)));
      board.append(quadrant);
    });
  }

  function rankedProblems() {
    return [...problems].sort((a, b) => score(b) - score(a));
  }

  function renderPriorityList() {
    const list = document.querySelector("#priorityList");
    list.replaceChildren();
    selectedProblemIds = rankedProblems().slice(0, Math.min(3, problems.length)).map((problem) => problem.id);
    rankedProblems().forEach((problem) => {
      const label = document.createElement("label");
      label.className = "priority-item";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.value = problem.id;
      checkbox.checked = selectedProblemIds.includes(problem.id);
      checkbox.addEventListener("change", () => {
        const checked = [...list.querySelectorAll("input:checked")];
        if (checked.length > 5) {
          checkbox.checked = false;
          return;
        }
        selectedProblemIds = checked.map((input) => input.value);
      });
      const copy = document.createElement("span");
      copy.innerHTML = `<strong>${problem.title}</strong><small>${problem.evidence || "No evidence entered yet."}</small>`;
      const tagRow = document.createElement("span");
      tagRow.className = "tag-row";
      tagsFor(problem).forEach((tag) => {
        const tagSpan = document.createElement("span");
        tagSpan.className = "mini-tag";
        tagSpan.textContent = tag;
        tagRow.append(tagSpan);
      });
      copy.append(tagRow);
      const scoreBadge = document.createElement("span");
      scoreBadge.className = "priority-score";
      scoreBadge.textContent = score(problem);
      label.append(checkbox, copy, scoreBadge);
      list.append(label);
    });
  }

  function interventionType(problem) {
    if (problem.cynefin === "simple") return "Standardise a known control or checklist.";
    if (problem.cynefin === "complicated") return "Use expert diagnosis, modelling, and framework selection.";
    if (problem.cynefin === "complex") return "Prototype, sensemake, learn, adapt, and scale carefully.";
    if (problem.cynefin === "chaotic") return "Stabilise the risk, preserve evidence, then investigate.";
    return "Run discovery to clarify ownership, data, language, and the correct route.";
  }

  function frameworkStack(problem) {
    const base = domainMethods[problem.domain];
    const route = problem.cynefin === "confused"
      ? "Materiality scan, stakeholder review, ownership mapping, data inventory."
      : `${spectrum[problem.spectrum].method} ${cynefin[problem.cynefin].method}`;
    return [base, route];
  }

  function decisionQuestions(problem) {
    const maturityQuestion = problem.spectrum === "light"
      ? "Is this mainly about reducing harm, standards, compliance, evidence, or transparency?"
      : problem.spectrum === "mid"
        ? "Is this mainly about redesigning value chains, business models, or cross-functional systems?"
        : "Is this mainly about regeneration, justice, nature, long-range futures, or social-ecological alignment?";
    const complexityQuestion = problem.cynefin === "simple"
      ? "Is the task clear, repeatable, owned, and based on known information?"
      : problem.cynefin === "complicated"
        ? "What expert judgement, framework, model, audit, or structured plan is needed?"
        : problem.cynefin === "complex"
          ? "What needs to be learned through a safe pilot before scaling?"
          : problem.cynefin === "chaotic"
            ? "What must be stabilised immediately before sense-making can begin?"
            : "Who owns this, what data exists, and what type of problem is it really?";
    return [maturityQuestion, complexityQuestion, "Where is uncertainty highest, and do we need more system mapping before prototyping?"];
  }

  function decisionTimeline(problem, stack, questions) {
    return [
      {
        step: "Start",
        label: "Problem",
        question: "Are we clear enough about the problem to route it?",
        answer: problem.evidence ? "Yes" : "Unsure",
        outcome: problem.evidence || "Capture the evidence or assumption before committing."
      },
      {
        step: "1",
        label: "Diagnose",
        question: `Is this primarily a ${problem.domain} problem?`,
        answer: "Selected route",
        outcome: stack[0]
      },
      {
        step: "2",
        label: "Classify",
        question: questions[0],
        answer: spectrum[problem.spectrum].label,
        outcome: spectrum[problem.spectrum].focus
      },
      {
        step: "3",
        label: "Complexity",
        question: questions[1],
        answer: cynefin[problem.cynefin].label,
        outcome: interventionType(problem)
      },
      {
        step: "4",
        label: "Confidence",
        question: questions[2],
        answer: problem.confidence <= 2 ? "More discovery" : "Ready to prototype",
        outcome: problem.confidence <= 2
          ? "Validate evidence, owners, and assumptions before major investment."
          : "Move into the next intervention or experiment design step."
      }
    ];
  }

  function routeExamples(problem) {
    return examplesByRoute[`${problem.spectrum}-${problem.cynefin}`] || examplesByRoute[`${problem.spectrum}-confused`] || [];
  }

  function opportunityResponse(problem) {
    if (problem.domain === "behaviour") return "Behaviour response: diagnose capability, opportunity, and motivation before designing nudges or training.";
    if (problem.domain === "product" || problem.domain === "material") return "Product/material response: compare alternatives, test lifecycle impact, and prototype lower-impact options.";
    if (problem.domain === "supply") return "Supply chain response: segment suppliers, request evidence, and build a joint improvement route.";
    if (problem.domain === "governance") return "Governance response: clarify decision rights, owners, review cadence, and escalation routes.";
    if (problem.domain === "reporting" || problem.domain === "data") return "Data response: build a source register, metric dictionary, evidence file, and confidence rating.";
    if (problem.domain === "business") return "Business model response: test circular, service, or value-driven models against viability and strategic fit.";
    return "Systems response: map actors, dependencies, leverage points, and intervention risks before prototyping.";
  }

  function pageSixHandoff(problem) {
    return {
      projectName: `${problem.title} intervention sprint`,
      chosenOpportunity: opportunityResponse(problem),
      timeline: problem.impact >= 4 && problem.effort <= 2
        ? "Immediate action candidate: define a 0-3 month pilot before larger planning."
        : "Strategy candidate: break into immediate discovery, mid-term design, and long-term implementation actions.",
      hypothesis: `If we address ${problem.title.toLowerCase()} using a ${cynefin[problem.cynefin].label.toLowerCase()} intervention route, then the organisation should improve ${problem.domain} performance with clearer evidence and ownership.`,
      success: problem.confidence <= 2
        ? "Success first means better evidence confidence, clearer ownership, and agreement on the right route."
        : "Success means measurable progress against impact, feasibility, stakeholder value, and strategic fit.",
      nextStep: problem.cynefin === "chaotic"
        ? "Stabilise the issue and create a decision record."
        : problem.cynefin === "confused"
          ? "Run a short discovery sprint to clarify owner, data, and business reason."
          : "Design the first prototype or intervention test."
    };
  }

  function renderHandoffPreview(selected) {
    const preview = document.querySelector("#handoffPreview");
    if (!preview) return;
    preview.replaceChildren();
    selected.forEach((problem) => {
      const handoff = pageSixHandoff(problem);
      const card = document.createElement("article");
      card.className = "handoff-card";
      card.innerHTML = `
        <p class="eyebrow">Page 6 handoff</p>
        <h3>${problem.title}</h3>
        <div class="handoff-grid">
          <div><strong>Problem statement</strong><p>${problem.evidence || "Evidence still needs to be clarified."}</p></div>
          <div><strong>Key opportunity</strong><p>${handoff.chosenOpportunity}</p></div>
          <div><strong>Timeline direction</strong><p>${handoff.timeline}</p></div>
          <div><strong>Prototype hypothesis</strong><p>${handoff.hypothesis}</p></div>
          <div><strong>Success measure direction</strong><p>${handoff.success}</p></div>
          <div><strong>Simple next step</strong><p>${handoff.nextStep}</p></div>
        </div>
      `;
      preview.append(card);
    });
  }

  function selectedProblems() {
    return selectedProblemIds.map((id) => problems.find((problem) => problem.id === id)).filter(Boolean);
  }

  function renderDecisionTrees() {
    const selected = selectedProblems();
    if (!selected.length) return;
    const list = document.querySelector("#decisionTreeList");
    list.replaceChildren();
    selected.forEach((problem) => {
      const tree = document.createElement("article");
      tree.className = "decision-tree";
      const stack = frameworkStack(problem);
      const questions = decisionQuestions(problem);
      const timeline = decisionTimeline(problem, stack, questions);
      const current = timeline[Math.min(2, timeline.length - 1)];
      const examples = routeExamples(problem);
      tree.innerHTML = `
        <div>
          <p class="eyebrow">Selected problem</p>
          <h3>${problem.title}</h3>
          <p>${problem.evidence || "Evidence still needs to be gathered."}</p>
        </div>
        <div class="decision-progress" aria-label="Decision tree progress">
          ${timeline.map((item, index) => `
            <div class="decision-progress-step ${index <= 2 ? "is-active" : ""}">
              <span>${item.step}</span>
              <strong>${item.label}</strong>
              <small>${item.answer}</small>
            </div>
          `).join("")}
        </div>
        <div class="guided-question-panel">
          <div>
            <p class="eyebrow">Current decision</p>
            <h3>${current.question}</h3>
            <p>${current.outcome}</p>
          </div>
          <div class="answer-chip-row" aria-label="Decision answer options">
            <span class="answer-chip">Yes</span>
            <span class="answer-chip">No</span>
            <span class="answer-chip is-selected">${current.answer}</span>
          </div>
        </div>
        <div class="tree-path">
          ${timeline.map((item) => `
            <div class="tree-node">
              <span>${item.step}. ${item.label}</span>
              <strong>${item.answer}</strong>
              <p>${item.outcome}</p>
            </div>
          `).join("")}
        </div>
        <div class="tree-details">
          <article><h3>Questions to ask next</h3><ul>${timeline.slice(2).map((item) => `<li>${item.question}</li>`).join("")}</ul></article>
          <article><h3>Relevant examples</h3><ul>${examples.map((item) => `<li>${item}</li>`).join("")}</ul></article>
          <article><h3>Process stack</h3><ul>${stack.map((item) => `<li>${item}</li>`).join("")}<li>${cynefin[problem.cynefin].method}</li></ul></article>
        </div>
      `;
      list.append(tree);
    });
    renderHandoffPreview(selected);
    localStorage.setItem("greenSpectrumSelectedProblems", JSON.stringify(selected));
    decisionSection.classList.remove("is-locked");
    decisionSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function appendItems(list, items, fallback) {
    list.replaceChildren();
    (items.length ? items : [fallback]).forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      list.append(li);
    });
  }

  function buildSortOutput() {
    const selected = selectedProblems();
    const selectedSummary = document.querySelector("#selectedProblemSummary");
    const interventionSummary = document.querySelector("#interventionSummary");
    const dataNeedSummary = document.querySelector("#sortDataNeedSummary");

    appendItems(
      selectedSummary,
      selected.map((problem) => `${problem.title}: priority score ${score(problem)}, ${spectrum[problem.spectrum].label}, ${cynefin[problem.cynefin].label}.`),
      "No selected problems yet."
    );
    appendItems(
      interventionSummary,
      selected.map((problem) => `${problem.title}: ${interventionType(problem)}`),
      "No intervention styles generated yet."
    );
    appendItems(
      dataNeedSummary,
      selected.map((problem) => {
        if (problem.confidence <= 2) return `${problem.title}: run discovery, validate evidence, and improve confidence before major investment.`;
        return `${problem.title}: prepare ${problem.domain} evidence, owner, success measure, and prototype assumption.`;
      }),
      "No data needs generated yet."
    );
    localStorage.setItem("greenSpectrumSortPrioritise", JSON.stringify({
      problems,
      selected,
      pageSixHandoff: selected.map((problem) => ({ problem, handoff: pageSixHandoff(problem) }))
    }));
    localStorage.setItem("greenSpectrumSortPrioritiseComplete", "true");
    outputSection.classList.remove("is-locked");
    sortState.textContent = "Sort and Prioritise completed. Page 6 is ready to design next.";
    outputSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  addButton.addEventListener("click", () => {
    problems.push({
      id: `problem-${Date.now()}`,
      title: "",
      evidence: "",
      domain: "systems",
      spectrum: "light",
      cynefin: "confused",
      impact: 3,
      effort: 3,
      strategic: 3,
      urgency: 3,
      confidence: 2,
      reflection: ""
    });
    renderProblemCards();
  });

  sortButton.addEventListener("click", () => {
    if (![...cardList.querySelectorAll("[data-field='title']")].every((input) => input.reportValidity())) return;
    collectProblems();
    renderHeatmap();
    renderSpectrumLanes();
    renderCynefinBoard();
    renderPriorityList();
    visualSection.classList.remove("is-locked");
    visualSection.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  decisionButton.addEventListener("click", renderDecisionTrees);

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    buildSortOutput();
  });

  try {
    problems = JSON.parse(localStorage.getItem("greenSpectrumSortProblems") || "[]");
  } catch (error) {
    problems = [];
  }
  if (!problems.length) problems = defaultProblems();
  renderProblemCards();
}

function initPrototypePage() {
  const form = document.querySelector("#prototypeForm");
  if (!form) return;

  const pathwayList = document.querySelector("#pathwayList");
  const horizonBoard = document.querySelector("#horizonBoard");
  const prototypeTypeGrid = document.querySelector("#prototypeTypeGrid");
  const experimentCardList = document.querySelector("#experimentCardList");
  const outputSection = document.querySelector("#prototype-output");
  const prototypeState = document.querySelector("#prototypeState");
  let pathways = [];
  let horizonPlans = [];
  let selectedPrototypeTypes = [];

  const prototypeTypes = [
    { key: "narrative", label: "Narrative Prototype", example: "Future press release", tests: "Stakeholder resonance and mission clarity.", dimensions: ["desirability", "impact"] },
    { key: "data", label: "Data Prototype", example: "Emissions tracker pilot or dynamic dashboard", tests: "System setup, input-output integrity, update logic, and confidence.", dimensions: ["feasibility", "adaptability"] },
    { key: "physical", label: "Physical Prototype", example: "Alternative packaging test", tests: "Technical workability, constraints, form, and durability.", dimensions: ["feasibility", "impact"] },
    { key: "process", label: "Process Prototype", example: "Logistics route or workflow test", tests: "Real-world execution, repeatability, training, and integration.", dimensions: ["feasibility", "scalability"] },
    { key: "behavioural", label: "Behavioural Prototype", example: "Energy-saving prompts", tests: "Motivation, friction, adoption, and everyday fit.", dimensions: ["desirability", "adaptability"] },
    { key: "experience", label: "Experience Prototype", example: "Walkthrough of a new customer journey", tests: "Emotional response, clarity, usability, and perceived value.", dimensions: ["desirability", "viability"] },
    { key: "cultural", label: "Cultural Prototype", example: "New sustainability rituals", tests: "Shared meaning, team adoption, and organisational readiness.", dimensions: ["adaptability", "scalability"] },
    { key: "business", label: "Business Model Prototype", example: "Service-as-a-product", tests: "Revenue, cost structure, stakeholder fit, and commercial logic.", dimensions: ["viability", "scalability"] },
    { key: "financial", label: "Financial or Policy Prototype", example: "Financial risk modelling", tests: "Economic trade-offs, investor perception, policy fit, and risk.", dimensions: ["viability", "impact"] },
    { key: "governance", label: "Governance Prototype", example: "ESG board role", tests: "Decision rights, structure adaptability, and scale to other teams.", dimensions: ["scalability", "adaptability"] },
    { key: "service", label: "Service Prototype", example: "Onboarding service", tests: "Iteration potential, service fit, and user evolution.", dimensions: ["desirability", "scalability"] },
    { key: "system", label: "System Prototype", example: "Circular economy pilot", tests: "Ripple effects, feedback loops, and system-level benefit.", dimensions: ["impact", "adaptability"] }
  ];

  const horizons = [
    { key: "h1", label: "Horizon 1", range: "0-3 months", scale: "Early rapid prototype", prompt: "What can we do now with minimal resources?" },
    { key: "h2", label: "Horizon 2", range: "3-12 months", scale: "Mid-scale pilot", prompt: "What takes more time, resources, and approval?" },
    { key: "h3", label: "Horizon 3", range: "12+ months", scale: "Full pilot or policy test", prompt: "What belongs to the longer strategic project?" }
  ];

  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function readable(value) {
    if (!value) return "";
    return String(value).replace(/(^|-)([a-z])/g, (_, dash, letter) => `${dash ? " " : ""}${letter.toUpperCase()}`);
  }

  function loadPathways() {
    try {
      const data = JSON.parse(localStorage.getItem("greenSpectrumSortPrioritise") || "{}");
      if (Array.isArray(data.selected) && data.selected.length) {
        return data.selected.map((problem, index) => {
          const handoff = (data.pageSixHandoff || []).find((item) => item.problem?.id === problem.id)?.handoff || {};
          return {
            id: problem.id || `pathway-${index}`,
            title: problem.title || `Priority problem ${index + 1}`,
            problemStatement: problem.evidence || "",
            greenStage: problem.spectrum || "mid",
            complexity: problem.cynefin || "complex",
            domain: problem.domain || "systems",
            desiredOutcome: handoff.success || "Measurable progress against impact, feasibility, stakeholder value, and strategic fit.",
            keyOpportunity: handoff.chosenOpportunity || "Translate the selected problem into a focused intervention pathway.",
            chosenSolution: "",
            winningAspiration: "",
            wherePlay: "",
            howWin: "",
            simpleNextStep: handoff.nextStep || "Design the first prototype or intervention test.",
            hypothesis: handoff.hypothesis || `If we address ${problem.title || "this problem"}, we should improve evidence, ownership, and impact.`
          };
        });
      }
    } catch (error) {
      return [];
    }
    return [];
  }

  function defaultPathways() {
    return [
      {
        id: "default-scope3",
        title: "Supplier emissions intervention sprint",
        problemStatement: "Supplier emissions data is incomplete, inconsistent, and difficult to verify.",
        greenStage: "light",
        complexity: "complex",
        domain: "supply",
        desiredOutcome: "Priority suppliers provide usable Scope 3 data with a clear confidence rating.",
        keyOpportunity: "Segment suppliers and run a supported data collection pilot.",
        chosenSolution: "Supplier data pack and engagement pilot.",
        winningAspiration: "Create a repeatable supplier emissions data process in one quarter.",
        wherePlay: "Top supplier categories by spend, material impact, and emissions risk.",
        howWin: "Make participation simple, commercially relevant, and evidence-based.",
        simpleNextStep: "Select the first supplier cohort.",
        hypothesis: "If suppliers receive a clear template and commercial rationale, then data quality and participation should improve."
      },
      {
        id: "default-packaging",
        title: "Packaging waste prototype pathway",
        problemStatement: "Packaging waste is visible across procurement, customer use, and end-of-life stages.",
        greenStage: "mid",
        complexity: "complicated",
        domain: "product",
        desiredOutcome: "A lower-impact packaging option is validated against cost, durability, user acceptance, and waste reduction.",
        keyOpportunity: "Test a material or packaging alternative before scaling.",
        chosenSolution: "Alternative packaging trial.",
        winningAspiration: "Reduce priority packaging waste while maintaining customer experience and operational fit.",
        wherePlay: "One high-volume product line or customer journey.",
        howWin: "Use evidence from LCA, procurement, operations, and customer feedback.",
        simpleNextStep: "Identify the packaging item and baseline impact.",
        hypothesis: "If we trial a lower-impact packaging format, then waste can fall without damaging cost, durability, or user value."
      }
    ];
  }

  function field(container, name) {
    return container.querySelector(`[data-field="${name}"]`);
  }

  function fieldValue(container, name) {
    return field(container, name)?.value.trim() || "";
  }

  function renderPathways() {
    pathwayList.replaceChildren();
    pathways.forEach((pathway, index) => {
      const card = document.createElement("article");
      card.className = "pathway-card";
      card.dataset.pathwayId = pathway.id;
      card.innerHTML = `
        <header>
          <div>
            <p class="eyebrow">Pathway ${String(index + 1).padStart(2, "0")}</p>
            <h3>${escapeHtml(pathway.title)}</h3>
            <p>${escapeHtml(pathway.problemStatement || "Problem statement needs to be clarified.")}</p>
          </div>
          <div class="pathway-meta">
            <span class="mini-tag">${escapeHtml(readable(pathway.greenStage))}</span>
            <span class="mini-tag">${escapeHtml(readable(pathway.complexity))}</span>
            <span class="mini-tag">${escapeHtml(readable(pathway.domain))}</span>
          </div>
        </header>
        <div class="pathway-fields">
          <label>Project name<input type="text" data-field="title" value="${escapeHtml(pathway.title)}"></label>
          <label>Desired outcome<textarea rows="4" data-field="desiredOutcome">${escapeHtml(pathway.desiredOutcome)}</textarea></label>
          <label>Key opportunity<textarea rows="4" data-field="keyOpportunity">${escapeHtml(pathway.keyOpportunity)}</textarea></label>
          <label>Chosen solution<textarea rows="4" data-field="chosenSolution">${escapeHtml(pathway.chosenSolution)}</textarea></label>
          <label>Winning aspiration<textarea rows="4" data-field="winningAspiration" placeholder="Example: reduce packaging waste by 50% in two years.">${escapeHtml(pathway.winningAspiration)}</textarea></label>
          <label>Where will we play?<textarea rows="4" data-field="wherePlay" placeholder="Geography, department, supply chain node, product line, user group.">${escapeHtml(pathway.wherePlay)}</textarea></label>
          <label>How will we win?<textarea rows="4" data-field="howWin" placeholder="Unique advantage, capability, relationship, evidence, or value proposition.">${escapeHtml(pathway.howWin)}</textarea></label>
          <label>Initial hypothesis<textarea rows="4" data-field="hypothesis">${escapeHtml(pathway.hypothesis)}</textarea></label>
        </div>
      `;
      pathwayList.append(card);
    });
  }

  function collectPathways() {
    pathways = [...pathwayList.querySelectorAll(".pathway-card")].map((card) => {
      const existing = pathways.find((item) => item.id === card.dataset.pathwayId) || {};
      return {
        ...existing,
        id: card.dataset.pathwayId,
        title: fieldValue(card, "title") || existing.title,
        desiredOutcome: fieldValue(card, "desiredOutcome"),
        keyOpportunity: fieldValue(card, "keyOpportunity"),
        chosenSolution: fieldValue(card, "chosenSolution"),
        winningAspiration: fieldValue(card, "winningAspiration"),
        wherePlay: fieldValue(card, "wherePlay"),
        howWin: fieldValue(card, "howWin"),
        hypothesis: fieldValue(card, "hypothesis")
      };
    });
    return pathways;
  }

  function defaultAction(pathway, horizon) {
    if (horizon.key === "h1") return pathway.simpleNextStep || "Run a rapid low-cost prototype and gather feedback.";
    if (horizon.key === "h2") return "Develop a mid-scale pilot with operational data, stakeholder validation, and approvals.";
    return "Prepare a full pilot, policy test, or strategic implementation case.";
  }

  function renderHorizonBoard() {
    horizonBoard.replaceChildren();
    horizonPlans = pathways.map((pathway) => ({
      id: pathway.id,
      title: pathway.title,
      horizons: horizons.map((horizon) => ({
        key: horizon.key,
        action: defaultAction(pathway, horizon),
        owner: "",
        kpi: "",
        outcome: horizon.key === "h1" ? pathway.desiredOutcome : "",
        resources: "",
        approval: ""
      }))
    }));

    horizonPlans.forEach((plan) => {
      const section = document.createElement("article");
      section.className = "horizon-problem";
      section.dataset.pathwayId = plan.id;
      section.innerHTML = `<header><p class="eyebrow">Backcasting pathway</p><h3>${escapeHtml(plan.title)}</h3></header>`;
      const grid = document.createElement("div");
      grid.className = "horizon-grid";
      plan.horizons.forEach((entry) => {
        const horizon = horizons.find((item) => item.key === entry.key);
        const card = document.createElement("section");
        card.className = "horizon-card";
        card.dataset.horizon = horizon.key;
        card.innerHTML = `
          <header><span>${horizon.label} / ${horizon.range}</span><h3>${horizon.scale}</h3><p>${horizon.prompt}</p></header>
          <label>Action<textarea rows="4" data-field="action">${escapeHtml(entry.action)}</textarea></label>
          <label>Expected outcome<textarea rows="3" data-field="outcome">${escapeHtml(entry.outcome)}</textarea></label>
          <label>KPI or success metric<input type="text" data-field="kpi" placeholder="Waste reduction %, uptake %, carbon reduction, participation rate."></label>
          <label>Process owner<input type="text" data-field="owner" placeholder="Name or role"></label>
          <label>Resources needed<textarea rows="3" data-field="resources"></textarea></label>
          <label>Approval or support needed<textarea rows="3" data-field="approval"></textarea></label>
        `;
        grid.append(card);
      });
      section.append(grid);
      horizonBoard.append(section);
    });
  }

  function collectHorizons() {
    horizonPlans = [...horizonBoard.querySelectorAll(".horizon-problem")].map((section) => ({
      id: section.dataset.pathwayId,
      title: pathways.find((pathway) => pathway.id === section.dataset.pathwayId)?.title || "Pathway",
      horizons: [...section.querySelectorAll(".horizon-card")].map((card) => ({
        key: card.dataset.horizon,
        action: fieldValue(card, "action"),
        outcome: fieldValue(card, "outcome"),
        kpi: fieldValue(card, "kpi"),
        owner: fieldValue(card, "owner"),
        resources: fieldValue(card, "resources"),
        approval: fieldValue(card, "approval")
      }))
    }));
    return horizonPlans;
  }

  function recommendedPrototypeKeys() {
    const keys = new Set(["data", "process", "system"]);
    pathways.forEach((pathway) => {
      if (pathway.domain === "behaviour") keys.add("behavioural");
      if (pathway.domain === "product" || pathway.domain === "material") keys.add("physical");
      if (pathway.domain === "business") keys.add("business");
      if (pathway.domain === "governance") keys.add("governance");
      if (pathway.domain === "supply") keys.add("process");
      if (pathway.complexity === "complex") keys.add("system");
      if (pathway.complexity === "complicated") keys.add("data");
      if (pathway.greenStage === "dark") keys.add("narrative");
    });
    return [...keys].slice(0, 6);
  }

  function renderPrototypeTypes() {
    prototypeTypeGrid.replaceChildren();
    selectedPrototypeTypes = recommendedPrototypeKeys();
    prototypeTypes.forEach((type) => {
      const label = document.createElement("label");
      label.className = "prototype-type-card";
      label.innerHTML = `
        <input type="checkbox" value="${type.key}" ${selectedPrototypeTypes.includes(type.key) ? "checked" : ""}>
        <span>
          <strong>${type.label}</strong>
          <small>${type.example}</small>
          <small>To test: ${type.tests}</small>
        </span>
        <span class="learning-dimensions">
          ${type.dimensions.map((dimension) => `<span class="mini-tag">${dimension}</span>`).join("")}
        </span>
      `;
      label.querySelector("input").addEventListener("change", () => {
        selectedPrototypeTypes = [...prototypeTypeGrid.querySelectorAll("input:checked")].map((input) => input.value);
      });
      prototypeTypeGrid.append(label);
    });
  }

  function renderExperimentCards() {
    experimentCardList.replaceChildren();
    if (!selectedPrototypeTypes.length) selectedPrototypeTypes = recommendedPrototypeKeys();
    pathways.forEach((pathway) => {
      const h1 = horizonPlans.find((plan) => plan.id === pathway.id)?.horizons.find((entry) => entry.key === "h1") || {};
      const card = document.createElement("article");
      card.className = "experiment-planner";
      card.dataset.pathwayId = pathway.id;
      card.innerHTML = `
        <div>
          <p class="eyebrow">Experiment card</p>
          <h3>${escapeHtml(pathway.title)}</h3>
          <p>${escapeHtml(pathway.hypothesis)}</p>
        </div>
        <div class="experiment-grid">
          <label>Experiment title<input type="text" data-field="experimentTitle" value="${escapeHtml(pathway.title)}"></label>
          <label>Empathy lens<select data-field="empathyLens"><option>Business</option><option>Human</option><option>Planetary</option></select></label>
          <label>Winning aspiration<textarea rows="4" data-field="winningAspiration">${escapeHtml(pathway.winningAspiration || pathway.desiredOutcome)}</textarea></label>
          <label>Capabilities required<textarea rows="4" data-field="capabilities" placeholder="Team, technology, partnerships, expertise, dashboards, rituals, check-ins."></textarea></label>
        </div>
        <fieldset>
          <legend>Prototype type</legend>
          <div class="experiment-type-checks">
            ${prototypeTypes.map((type) => `
              <label><input type="checkbox" value="${type.key}" ${selectedPrototypeTypes.includes(type.key) ? "checked" : ""}> ${type.label}</label>
            `).join("")}
          </div>
        </fieldset>
        <div class="decision-logic-grid">
          <label>We will know the result is positive if<textarea rows="3" data-field="positiveIf">${escapeHtml(h1.kpi ? `${h1.kpi} improves and stakeholders can explain why.` : "The KPI improves and stakeholders value the change.")}</textarea></label>
          <label>If positive, we will<textarea rows="3" data-field="positiveThen">Scale, build the next prototype, or develop the business case.</textarea></label>
          <label>We will know the result is negative if<textarea rows="3" data-field="negativeIf">The test creates unacceptable cost, harm, friction, or weak evidence.</textarea></label>
          <label>If negative, we will<textarea rows="3" data-field="negativeThen">Reframe, redesign, or test in a new context.</textarea></label>
          <label>If inconclusive, we will<textarea rows="3" data-field="inconclusiveThen">Gather further data or refine the hypothesis.</textarea></label>
          <label>Who will be affected?<textarea rows="3" data-field="stakeholders" placeholder="Teams, suppliers, customers, communities, partners, non-human stakeholders."></textarea></label>
        </div>
        <div class="governance-grid">
          <label>Key metrics or KPIs<input type="text" data-field="metrics" value="${escapeHtml(h1.kpi)}"></label>
          <label>Measurement method<input type="text" data-field="method" placeholder="Survey, LCA, sensor data, interview, dashboard, forms."></label>
          <label>Time frame<input type="text" data-field="timeframe" placeholder="Start date to end date"></label>
          <label>Observation frequency<input type="text" data-field="frequency" placeholder="Daily, weekly, monthly"></label>
          <label>Project owner<input type="text" data-field="owner" value="${escapeHtml(h1.owner)}"></label>
          <label>Support team<input type="text" data-field="support" placeholder="UX, operations, legal, finance, external partners."></label>
          <label>Budget estimate<input type="text" data-field="budget"></label>
          <label>Accountability lead<input type="text" data-field="accountability"></label>
          <label>Success criteria<textarea rows="3" data-field="successCriteria">${escapeHtml(h1.outcome || pathway.desiredOutcome)}</textarea></label>
          <label>Failure criteria<textarea rows="3" data-field="failureCriteria"></textarea></label>
          <label>Learning regardless<textarea rows="3" data-field="learningRegardless">${escapeHtml(pathway.keyOpportunity)}</textarea></label>
          <label>Riskiest assumption<textarea rows="3" data-field="riskiestAssumption"></textarea></label>
          <label class="confidence-row">Confidence score<input type="number" min="1" max="10" data-field="confidence" value="6"></label>
          <label>Next review date<input type="date" data-field="nextReview"></label>
        </div>
      `;
      experimentCardList.append(card);
    });
  }

  function collectExperimentCards() {
    return [...experimentCardList.querySelectorAll(".experiment-planner")].map((card) => ({
      id: card.dataset.pathwayId,
      title: fieldValue(card, "experimentTitle"),
      empathyLens: fieldValue(card, "empathyLens"),
      prototypeTypes: [...card.querySelectorAll(".experiment-type-checks input:checked")].map((input) => input.value),
      winningAspiration: fieldValue(card, "winningAspiration"),
      capabilities: fieldValue(card, "capabilities"),
      positiveIf: fieldValue(card, "positiveIf"),
      positiveThen: fieldValue(card, "positiveThen"),
      negativeIf: fieldValue(card, "negativeIf"),
      negativeThen: fieldValue(card, "negativeThen"),
      inconclusiveThen: fieldValue(card, "inconclusiveThen"),
      stakeholders: fieldValue(card, "stakeholders"),
      metrics: fieldValue(card, "metrics"),
      method: fieldValue(card, "method"),
      timeframe: fieldValue(card, "timeframe"),
      frequency: fieldValue(card, "frequency"),
      owner: fieldValue(card, "owner"),
      support: fieldValue(card, "support"),
      budget: fieldValue(card, "budget"),
      accountability: fieldValue(card, "accountability"),
      successCriteria: fieldValue(card, "successCriteria"),
      failureCriteria: fieldValue(card, "failureCriteria"),
      learningRegardless: fieldValue(card, "learningRegardless"),
      riskiestAssumption: fieldValue(card, "riskiestAssumption"),
      confidence: fieldValue(card, "confidence"),
      nextReview: fieldValue(card, "nextReview")
    }));
  }

  function appendItems(list, items, fallback) {
    list.replaceChildren();
    (items.length ? items : [fallback]).forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      list.append(li);
    });
  }

  function addDefinition(list, term, value) {
    const dt = document.createElement("dt");
    dt.textContent = term;
    const dd = document.createElement("dd");
    dd.textContent = value || "Not provided yet";
    list.append(dt, dd);
  }

  function buildPrototypeOutput() {
    const experiments = collectExperimentCards();
    const horizonSummary = document.querySelector("#horizonSummary");
    const portfolioSummary = document.querySelector("#prototypePortfolioSummary");
    const governanceSummary = document.querySelector("#governanceSummary");
    const learningSummary = document.querySelector("#learningPathwaySummary");

    appendItems(
      horizonSummary,
      horizonPlans.flatMap((plan) => plan.horizons.map((entry) => {
        const horizon = horizons.find((item) => item.key === entry.key);
        return `${plan.title} - ${horizon.label}: ${entry.action || "No action set"} ${entry.kpi ? `KPI: ${entry.kpi}.` : ""}`;
      })),
      "No horizon strategy generated yet."
    );

    appendItems(
      portfolioSummary,
      experiments.map((experiment) => {
        const labels = experiment.prototypeTypes.map((key) => prototypeTypes.find((type) => type.key === key)?.label || key).join(", ");
        return `${experiment.title}: ${labels || "No prototype selected"}. Confidence ${experiment.confidence || "not scored"} / 10.`;
      }),
      "No prototype portfolio generated yet."
    );

    appendItems(
      governanceSummary,
      experiments.map((experiment) => {
        return `${experiment.title}: owner ${experiment.owner || "not assigned"}, accountability ${experiment.accountability || "not assigned"}, KPI ${experiment.metrics || "not defined"}.`;
      }),
      "No governance summary generated yet."
    );

    learningSummary.replaceChildren();
    experiments.forEach((experiment) => {
      addDefinition(learningSummary, `${experiment.title} - positive`, experiment.positiveThen);
      addDefinition(learningSummary, `${experiment.title} - negative`, experiment.negativeThen);
      addDefinition(learningSummary, `${experiment.title} - inconclusive`, experiment.inconclusiveThen);
    });

    localStorage.setItem("greenSpectrumPrototypeInterventions", JSON.stringify({
      pathways,
      horizonPlans,
      experiments
    }));
    localStorage.setItem("greenSpectrumPrototypeInterventionsComplete", "true");
    outputSection.classList.remove("is-locked");
    prototypeState.textContent = "Prototyping Interventions completed. The innovation portfolio is ready for review.";
    outputSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  form.querySelectorAll("[data-complete-prototype-step]").forEach((button) => {
    button.addEventListener("click", () => {
      const current = Number(button.dataset.completePrototypeStep);
      const next = Number(button.dataset.nextPrototypeStep);
      if (current === 1) {
        collectPathways();
        renderHorizonBoard();
      }
      if (current === 2) {
        collectHorizons();
        renderPrototypeTypes();
      }
      if (current === 3) {
        selectedPrototypeTypes = [...prototypeTypeGrid.querySelectorAll("input:checked")].map((input) => input.value);
        renderExperimentCards();
      }
      const currentSection = document.querySelector(`[data-prototype-step="${current}"]`);
      const nextSection = document.querySelector(`[data-prototype-step="${next}"]`);
      if (currentSection) currentSection.classList.add("is-complete");
      if (nextSection) {
        nextSection.classList.remove("is-locked");
        nextSection.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    buildPrototypeOutput();
  });

  pathways = loadPathways();
  if (!pathways.length) pathways = defaultPathways();
  renderPathways();
}

window.addEventListener("scroll", updateScrollProgress, { passive: true });
window.addEventListener("resize", updateScrollProgress);

initLandingPage();
initOnboardingPage();
initExploreMapPage();
initImpactJourneyPage();
initSortPrioritisePage();
initPrototypePage();
updateScrollProgress();
