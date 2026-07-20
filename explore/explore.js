const maturityLevels = [
  ["white", "White"],
  ["light", "Light Green"],
  ["mid", "Mid Green"],
  ["dark", "Dark Green"],
  ["unknown", "Not known"]
];

const questions = [
  q(1, "business", "Strategy and Positioning", "Strategy and Purpose", "Is sustainability embedded in strategic vision?", ["No stated goals", "Compliance-driven mission", "Purpose integrates across departments", "Regenerative, mission-led and ecosystem-restoring"], ["What are our core strategic objectives?", "How do they align with sustainability imperatives?", "What is the organisation’s current sustainability ambition?", "How would a regenerative strategy change market position?", "What disruptions or opportunities are emerging in the sector?"], ["corporate strategy", "annual report", "sustainability strategy", "board papers", "investor materials", "executive interviews", "departmental objectives"], ["Playing to Win Strategy Cascade", "PESTLE or STEEPV", "Scenario Planning", "Three Horizons", "Strategic Assumptions Mapping", "ESG Benchmarking", "Strategic Risk Radar"]),
  q(2, "business", "Strategy and Positioning", "Governance and Leadership", "How is sustainability governed?", ["No governance assigned", "Board-level oversight", "Embedded in executive performance", "Leadership acts as public transformation advocates"], ["Who owns sustainability?", "Where does decision authority sit?", "How are leaders held accountable?", "How is sustainability represented in executive incentives?", "Who are the formal and informal sponsors?"], ["governance structure", "board committee terms", "executive KPIs", "remuneration reports", "role descriptions", "leadership interviews"], ["Governance Mapping", "Power and Influence Matrix", "Leadership Alignment Interviews", "Responsibility Assignment Matrix"]),
  q(3, "business", "Strategy and Positioning", "Culture and Engagement", "How embedded is sustainability in daily behaviour?", ["No awareness", "Ad-hoc training", "Structured engagement and champions", "Regenerative culture and shared ownership"], ["How is sustainability discussed in everyday work?", "Are staff expected and enabled to act?", "What behaviours are rewarded?", "Where does engagement stop?", "What repeated organisational rituals reinforce or weaken sustainability?"], ["staff surveys", "training records", "internal communications", "performance frameworks", "employee interviews", "culture assessments"], ["Cultural Iceberg", "Change Readiness Assessment", "Behavioural Insight Mapping", "Organisational Ritual Mapping"]),
  q(4, "business", "Governance, Risk and Accountability", "Materiality and Risk", "How are material issues and systemic risks mapped?", ["No mapping", "One-time assessment", "Dynamic systems tools are used", "Full feedback loops connect decisions with planetary boundaries"], ["What issues have been identified as material?", "Who participated in that judgement?", "How frequently is the assessment updated?", "Are environmental and social risks linked?", "Are systemic and long-term risks considered?"], ["materiality assessment", "risk register", "enterprise risk process", "stakeholder research", "scenario analysis", "audit reports"], ["Double Materiality Assessment", "ESG Risk Heatmap", "Systems Mapping", "Risk Constellation Mapping", "Strategic Risk Radar"]),
  q(5, "business", "Governance, Risk and Accountability", "Transparency and Accountability", "How transparent is performance?", ["No disclosures", "Basic ESG reports", "Real-time, verified metrics", "Open data and participatory auditing"], ["What is disclosed internally and externally?", "Which claims are independently verified?", "Who can challenge performance?", "How are failures and limitations communicated?", "Is evidence accessible to affected stakeholders?"], ["ESG reports", "annual reports", "assurance statements", "dashboards", "audit processes", "public disclosures"], ["Disclosure Gap Analysis", "Accountability Mapping", "ESG Reporting Dashboard", "Participatory Audit Design"]),
  q(6, "business", "Governance, Risk and Accountability", "Metrics and Impact", "Are metrics focused on impact?", ["Only financial performance is tracked", "Scope 1 and Scope 2 are tracked", "Scope 3, social and biodiversity impacts are tracked", "Regeneration, wellbeing and community wealth are measured"], ["What outcomes are measured?", "Which metrics describe activity rather than impact?", "What remains unmeasured?", "How are environmental, social and financial outcomes connected?", "Which metrics influence decisions?"], ["KPI dashboards", "carbon inventory", "impact reports", "social-value reports", "biodiversity assessments", "finance systems"], ["Theory of Change", "Impact Measurement Framework", "Scope 1–3 Accounting", "Natural and Social Capital Assessment", "Balanced Scorecard"]),
  q(7, "business", "Value Creation, Products and Operations", "Product and Service Innovation", "Are products influenced by sustainability?", ["Profit-focused design", "Eco-efficiency improvements", "Circular design principles are adopted", "Products restore ecosystems and enable communities"], ["Which products or services conflict with sustainability goals?", "Where are sustainability criteria used in design decisions?", "How are customer needs and ecological outcomes balanced?", "Which offerings may become obsolete?", "What new value propositions are possible?"], ["product portfolio", "innovation pipeline", "design briefs", "customer research", "product LCA", "R&D strategy"], ["Circular Design", "Product Portfolio Mapping", "Life-Cycle Assessment", "Flourishing Business Canvas", "Sustainable Value Proposition Design"]),
  q(8, "business", "Value Creation, Products and Operations", "Operations and Circularity", "How embedded is sustainability in operations?", ["Sustainability is external to operations", "Certifications and audits are in place", "The supply chain is circular, resilient and traceable", "Operations are closed-loop, zero-waste and ecosystem-restorative"], ["What does the current value chain look like?", "Where are the high-impact or high-risk activities?", "Which activities are resource-intensive?", "Where is the organisation vulnerable to disruption?", "How could operational flows be redesigned?"], ["process maps", "supplier data", "procurement systems", "waste records", "logistics data", "operational audits", "certification records"], ["Value Chain Mapping", "Material Flow Analysis", "Systems Mapping", "Supply Chain Emissions Mapping", "Circular Value Chain Canvas"]),
  q(9, "business", "Finance, Data and Regulation", "Finance and Investment", "Are finances aligned with regeneration?", ["No sustainability budgets", "Green bonds or ESG screens are used", "Carbon pricing and impact-first investment are used", "Capital is directed towards ecosystem repair and social innovation"], ["Which revenue streams conflict with sustainability goals?", "What is the cost of inaction?", "What financial opportunities exist?", "How are sustainability risks priced?", "What return is expected from transformation?"], ["budgets", "capital allocation", "investment criteria", "business cases", "internal carbon price", "finance strategy", "insurance costs"], ["Cost–Benefit Analysis", "Environmental Profit and Loss", "Value Driver Tree", "Cash-Flow Analysis", "Monte Carlo Risk Analysis", "Opportunity Portfolio Mapping"]),
  q(10, "business", "Finance, Data and Regulation", "Data and Digital", "How is digital technology used for sustainability?", ["No data captured", "Basic tracking platforms", "Integrated real-time ESG systems", "AI and digital twins support regenerative modelling"], ["What sustainability data is available?", "Where is data fragmented?", "Who owns it?", "How reliable and timely is it?", "Which decisions could improved data support?"], ["data architecture", "ESG platforms", "operational systems", "spreadsheets", "data dictionaries", "digital strategy", "system-owner interviews"], ["Data Maturity Assessment", "Information Flow Mapping", "ESG Data Architecture", "Digital Twin Feasibility", "Data Confidence Matrix"]),
  q(11, "business", "Finance, Data and Regulation", "Policy and Regulation", "How does the organisation engage with policy?", ["No policy awareness", "Compliance with existing frameworks", "Strategy is aligned with future policy shifts", "The organisation contributes to regenerative legislation"], ["Which current regulations affect the organisation?", "Which upcoming requirements may change operations?", "Is the organisation prepared for disclosure and double materiality?", "What evidence systems are needed?", "Does policy engagement support or obstruct sustainability?"], ["compliance register", "legal advice", "public-policy team", "reporting standards", "industry association briefings", "risk register"], ["PESTLE Regulatory Lens", "Regulatory Horizon Scan", "CSRD or ISSB Diagnostic", "Compliance Audit", "ESG Risk Heatmap"]),
  q(12, "business", "Partnerships, Innovation and Adaptation", "Collaboration and Partnerships", "How strategic are sustainability partnerships?", ["The organisation operates in isolation", "The organisation is a member of networks", "Strategic alliances support circular infrastructure", "The organisation builds coalitions for system transformation"], ["Which challenges cannot be solved alone?", "What partnerships already exist?", "Where are incentives aligned or misaligned?", "Who controls necessary infrastructure?", "Which coalitions could increase leverage?"], ["partnership agreements", "industry memberships", "supplier programmes", "innovation consortia", "stakeholder maps", "public commitments"], ["Ecosystem Mapping", "Partnership Portfolio", "Stakeholder Network Analysis", "Collective Impact Framework"]),
  q(13, "business", "Partnerships, Innovation and Adaptation", "Innovation and R&D Alignment", "Is innovation directed towards sustainability?", ["Profit-driven R&D", "Incremental sustainability innovations", "Circular and inclusive R&D across departments", "Regenerative, mission-led innovation"], ["How are sustainability opportunities identified?", "What proportion of R&D supports environmental or social goals?", "How are ideas selected?", "What blocks internal innovation?", "How are experiments funded?"], ["R&D portfolio", "innovation strategy", "product pipeline", "investment criteria", "idea-management systems", "innovation-team interviews"], ["Innovation Portfolio Mapping", "Mission-Oriented Innovation", "Assumptions Mapping", "Three Horizons", "Innovation Readiness Assessment"]),
  q(14, "business", "Partnerships, Innovation and Adaptation", "Learning and Adaptation", "How does the organisation learn and adapt?", ["No learning systems", "Basic sustainability training", "Ongoing feedback loops and data tools", "Regenerative learning cycles and reflective practice"], ["How are lessons captured?", "Are failed initiatives reviewed?", "How quickly can strategy change?", "Where does knowledge remain siloed?", "How are new capabilities developed?"], ["training records", "project reviews", "learning systems", "communities of practice", "after-action reviews", "internal knowledge platforms"], ["Organisational Learning Loop", "After-Action Review", "Capability Maturity Mapping", "Reflective Practice", "Learning Portfolio"]),
  q(15, "business", "Partnerships, Innovation and Adaptation", "Crisis Readiness and Resilience", "Is the organisation ready for disruptions?", ["No adaptation strategy", "Contingency plans for known risks", "Stress testing and adaptive planning", "Distributed and antifragile systems thrive under uncertainty"], ["Which ecological, social or economic shocks matter most?", "What dependencies create vulnerability?", "Are climate and supply-chain risks connected?", "How rapidly can operations adapt?", "Which capabilities increase resilience?"], ["business continuity plans", "climate-risk assessment", "insurance data", "stress tests", "supply-chain risk analysis", "scenario plans"], ["Scenario Planning", "Resilience Diagnostic", "Cross-Impact Analysis", "Polycrisis Mapping", "Futures Wheel"]),
  q(16, "business", "Business Identity Review", "Regenerative Business Identity", "Is the business redefining its role in a planetary emergency?", ["Profit-maximising actor", "Risk-driven sustainability response", "Purpose-led circular-economy exemplar", "Movement partner, moral actor and ecological trustee"], ["What role does the organisation believe it plays in society?", "Whose wellbeing is included in its definition of value?", "Is nature treated as a stakeholder?", "What responsibilities extend beyond compliance?", "What would ecological trusteeship require?"], ["purpose statement", "governance principles", "public commitments", "leadership narratives", "stakeholder policies", "investment decisions"], ["Corporate Purpose Analysis", "Regenerative Business Maturity Framework", "Stakeholder Governance", "Nature as Stakeholder", "Future-State Narrative"]),
  q(17, "human", "Stakeholder Engagement and Inclusion", "Stakeholder Engagement", "How are stakeholders shaping the agenda?", ["Passive recipients", "Surveys and reports", "Regular co-creation sessions", "Long-term participatory governance"], ["Who defines the agenda?", "Who approves priorities?", "Who holds relevant knowledge?", "Who experiences consequences?", "Who has high influence but low accountability?", "Who has high exposure but little influence?", "Which groups are missing?", "Is engagement before or after decisions?", "Does stakeholder input change decisions?", "Does the organisation report back?", "Are power differences recognised?", "Are nature and future generations represented?"], ["stakeholder register", "consultations", "surveys", "interviews", "workshop outputs", "governance documents", "community forums", "employee forums", "supplier forums", "complaints", "grievance mechanisms", "decision logs"], ["Stakeholder Discovery Matrix", "Power and Influence Matrix", "Organisational Network Analysis", "Empathy Mapping", "Inclusion Gap Analysis", "Participatory Systems Mapping", "Personas", "Stakeholder Journey Maps", "Leadership Alignment Interviews", "Strategic Narrative Mapping"]),
  q(18, "human", "Employee Culture, Attitudes and Resistance", "Behavioural Change and Incentives", "How are employees enabled to act?", ["No connection to roles or performance", "Basic training offered", "Sustainability linked to performance", "Regenerative leadership and peer learning embedded"], ["What do staff believe about sustainability?", "How do they understand or misunderstand ESG?", "What emotional barriers exist?", "Are roles clear?", "Do people have authority, time and resources?", "What behaviours are rewarded?", "Which incentives undermine change?", "Does leadership model expectations?", "Is sustainability in performance review?", "Are champions supported?", "Is psychological safety sufficient?", "How is change fatigue managed?", "Are failures treated as learning?"], ["employee surveys", "interviews", "job descriptions", "KPIs", "incentive structures", "training", "internal communications", "performance reviews", "behavioural data", "meeting observation"], ["Cultural Iceberg Analysis", "Change Readiness Assessment", "Staff Survey Design", "Sensemaking Interviews", "Behavioural Insight Mapping", "COM-B", "Organisational Ritual Mapping", "Psychological Safety Mapping", "Power and Influence Matrix", "Force-Field Analysis"]),
  q(19, "human", "Internal Innovation and Co-creation Potential", "Customer Engagement", "How are customers empowered?", ["No sustainability communication", "Product badges or claims", "Education and decision tools", "Co-creation of regenerative solutions"], ["What information do customers receive?", "Is it understandable and verified?", "Are trade-offs visible?", "Are sustainable options accessible and affordable?", "Is responsibility shifted onto customers?", "How do price and design shape behaviour?", "Can customers challenge claims?", "Does customer evidence influence design?", "Are excluded or vulnerable customers considered?", "Are repair, reuse and take-back supported?", "Are rebound effects considered?"], ["customer interviews", "surveys", "complaints", "returns", "service analytics", "labels", "marketing", "claims assurance", "accessibility reviews", "repair and take-back data"], ["Customer Journey Mapping", "Service Blueprinting", "Empathy Mapping", "Behavioural Design", "Claims Audit", "User Research", "Participatory Design", "Accessibility Review", "Choice Architecture", "Circular Customer Journey"]),
  q(20, "human", "Skills, Capability and Learning Readiness", "Human and Community Wellbeing", "How is wellbeing supported internally and externally?", ["No wellbeing or equity focus", "Standard benefits and CSR", "Living wages and equity assessments", "Long-term partnerships regenerate communities"], ["How does work affect health and wellbeing?", "Are workloads and conditions sustainable?", "Are wages fair?", "Are contractors and supply-chain workers included?", "Which communities are affected?", "What value is created locally?", "What harms are externalised?", "Are livelihoods strengthened or displaced?", "Are grievance mechanisms accessible?", "Who carries transition costs?", "Are community partnerships long term?", "Are social impacts connected to core operations?"], ["wellbeing data", "health and safety", "absence and retention", "wages", "supplier audits", "human-rights due diligence", "community consultation", "grievance records", "social-impact reports"], ["Social Impact Assessment", "Social Life-Cycle Assessment", "Wellbeing Framework", "Community Wealth Building", "Human-Rights Impact Assessment", "Worker Journey Mapping", "Place-Based Systems Mapping", "Community Partnership Mapping"]),
  q(21, "human", "Stakeholder Engagement and Inclusion", "Equity, Justice and Inclusion", "How is justice embedded in sustainability efforts?", ["No DEI considerations", "Diversity pledges or training", "Equity-centred design and justice procurement", "Anti-oppressive, intersectional systems change is co-led"], ["Who benefits?", "Who bears costs?", "Which groups face greater exposure?", "Which voices are absent?", "Are impacts disaggregated?", "Is accessibility embedded?", "Are procurement practices justice-aware?", "Are grievance systems trusted?", "Who defines success?", "Who controls evidence?", "Is participation unpaid or extractive?", "Are transition plans just?", "Can affected groups co-lead decisions?", "Are intersectional effects considered?"], ["workforce demographics", "pay gaps", "progression", "accessibility", "procurement", "grievance data", "human-rights due diligence", "representation data", "community research", "equality assessments"], ["Equity-Centred Design", "Justice Impact Assessment", "Equality Impact Assessment", "Intersectional Stakeholder Mapping", "Inclusion Gap Analysis", "Participatory Governance", "Just Transition Assessment", "Accessibility Review", "Human-Rights Impact Assessment", "Power Mapping"]),
  q(22, "planetary", "Ecosystems and Planetary Boundaries", "Ecosystem Stewardship", "Is ecological regeneration supported?", ["No involvement", "Offsets or biodiversity pledges", "Active regeneration projects", "Place-based stewardship and infrastructure investment"], ["Which ecosystems does the organisation affect or depend on?", "Where is ecological harm occurring?", "Are activities restorative or compensatory?", "Which local places require stewardship?", "How could operations contribute to ecological recovery?"], ["biodiversity assessment", "site data", "nature-risk analysis", "land-use records", "restoration projects", "local ecological research"], ["Ecosystem Services Mapping", "Nature-Risk Assessment", "Nature-Based Solutions Portfolio", "Place-Based Systems Mapping", "Regenerative Design"]),
  q(23, "planetary", "Value Chain and Materials", "Value Chain and Traceability", "How aligned and traceable are partners?", ["Focus on cost and delivery", "Supplier codes and audits", "Full traceability across the supply chain", "Co-governance with regenerative suppliers"], ["What raw materials are used?", "Where do they come from?", "Which suppliers create the greatest impact or risk?", "What remains untraceable?", "How could suppliers participate in system redesign?"], ["procurement systems", "supplier records", "chain-of-custody data", "certifications", "audit reports", "logistics data", "contracts"], ["Value Chain Mapping", "Supply Chain Traceability", "Scope 3 Mapping", "Supplier Segmentation", "Materiality Mapping"]),
  q(24, "planetary", "Value Chain and Materials", "Circular Design and Materials", "Are materials and design circular?", ["No guidance or life-cycle thinking", "Single-attribute improvements", "Circularity design frameworks are used", "Biomimicry and net-positive materials are applied"], ["What materials does the organisation depend on?", "Are they finite, toxic, renewable or ethical?", "Where is waste generated?", "What happens at end of life?", "Where could loops be closed?"], ["bills of materials", "product specifications", "waste records", "LCA", "supplier data", "product returns", "end-of-life research"], ["Life-Cycle Assessment", "Material Flow Analysis", "Circularity Opportunity Mapping", "Cradle to Cradle", "Circular Value Chain Canvas"]),
  q(25, "planetary", "Climate, Nature and Regenerative Potential", "Climate and Biodiversity Integration", "How embedded are climate and nature in decisions?", ["No consideration", "Carbon reporting and disclosure", "Science-based targets and nature-positive principles", "Regenerative action drives investment"], ["What are the organisation’s most significant emissions and ecological impacts?", "Are climate and biodiversity considered together?", "Which planetary systems are affected?", "What ecological shocks could destabilise the organisation?", "What adaptive capacity exists?", "Can operations become net-positive?"], ["carbon inventory", "Scope 1–3 data", "biodiversity assessment", "climate-risk analysis", "water and land data", "science-based targets", "investment criteria"], ["Planetary Boundaries", "Doughnut Economics", "Scope 1–3 Carbon Accounting", "Climate Scenario Analysis", "Ecosystem Services Mapping", "Backcasting from Regenerative Futures"])
];

function q(id, empathy, theme, area, question, levels, discovery, evidence, tools) {
  return { id, empathy, theme, area, question, levels, discovery, evidence, tools };
}

const empathyMeta = {
  business: { title: "Business Empathy", copy: "Explore strategy, finance, operations, competitive positioning, risk, regulatory readiness and value creation.", time: "15–30 minutes" },
  human: { title: "Human Empathy", copy: "Coming next: culture, leadership, motivation, skills, behaviour, inclusion, engagement and organisational power.", time: "Next layer" },
  planetary: { title: "Planetary Empathy", copy: "Coming later: environmental impact, material flows, climate, biodiversity, planetary boundaries, resilience and regeneration.", time: "Future layer" }
};

const businessDiscoveryDomains = {
  "Strategic Alignment and Positioning": [1, 2, 4, 15, 16],
  "Value Chain Mapping and Leverage": [4, 7, 8, 12, 15],
  "Business Model and Financial Implications": [1, 7, 9, 13, 16],
  "Regulatory and Compliance Landscape": [4, 5, 6, 10, 11],
  "Benchmarking and Sector Comparison": [1, 5, 6, 7, 13, 16]
};

const humanDiscoveryDomains = {
  "Leadership, Governance and Influence": [17, 18],
  "Employee Culture, Attitudes and Resistance": [18, 20],
  "Skills, Capability and Learning Readiness": [18, 20],
  "Internal Innovation and Co-creation Potential": [17, 18, 19],
  "Stakeholder Engagement and Inclusion": [17, 19, 20, 21]
};

const planetaryDiscoveryDomains = {
  "Lifecycle and Ecological Impact": [22, 23, 24, 25],
  "Material Use and Circular Economy": [23, 24],
  "Planetary Systems Alignment": [22, 25],
  "Regeneration and Net-Positive Pathways": [22, 24, 25],
  "Systemic Risk and Resilience": [22, 23, 25]
};

const representationStatuses = ["Direct evidence", "Indirect evidence", "Not represented", "Outside scope", "Unclear"];
const influenceLevels = ["High influence", "Medium influence", "Low influence", "No influence", "Unclear"];
const impactExposureLevels = ["High exposure", "Medium exposure", "Low exposure", "Not exposed", "Unclear"];

const stakeholderOptions = ["Board", "Executive leadership", "Finance", "Operations", "Strategy", "Risk or legal", "Procurement", "Product or service teams", "Data or digital", "People or HR", "Customers", "Suppliers", "Investors", "Regulators", "Communities", "Nature or ecosystems"];
const systemOptions = ["Stakeholder", "Decision", "Policy", "Activity", "Metric", "Evidence", "Risk", "Value-chain stage", "Resource", "External dependency", "Feedback loop", "Delayed effect", "Incentive", "Unintended consequence"];
const carryForwardOptions = [
  ["save_insight", "Save as insight"],
  ["problem_signal", "Create problem signal"],
  ["evidence_task", "Create evidence task"],
  ["impact_journey", "Mark for Impact Journey"],
  ["human_empathy", "Mark for Human Empathy"],
  ["planetary_empathy", "Mark for Planetary Empathy"],
  ["dismiss", "Dismiss"]
];

const toolDefaults = {
  "Playing to Win Strategy Cascade": ["Strategic decision tool", "Clarifies where sustainability belongs in ambition, choices and competitive position.", "Corporate strategy, market position, leadership assumptions", "Strategy cascade and assumptions to test", "45-90 minutes", "Team or facilitation", "Downloadable guidance"],
  "PESTLE or STEEPV": ["External context scan", "Surfaces regulatory, technological, ecological and social forces that may shift priorities.", "Sector, markets, geography and horizon", "External pressures and opportunities map", "30-60 minutes", "Solo or team", "Guidance only"],
  "Scenario Planning": ["Future uncertainty tool", "Tests how the answer changes under different disruptions or market futures.", "Critical uncertainties, trends and risks", "Scenario implications and watchpoints", "60-120 minutes", "Team", "Guidance only"],
  "Three Horizons": ["Transformation timing tool", "Separates current optimisation from transition moves and regenerative futures.", "Current initiatives, emerging innovations and long-term ambition", "Horizon map", "45-90 minutes", "Team", "Downloadable guidance"],
  "Strategic Assumptions Mapping": ["Assumption test", "Finds hidden assumptions behind strategy, investment and delivery confidence.", "Known assumptions, decision records and evidence gaps", "Assumption register", "30-60 minutes", "Solo or team", "Interactive planned"],
  "ESG Benchmarking": ["Sector comparison", "Compares internal claims and maturity against peers or sector leaders.", "Peer set, disclosures and benchmark criteria", "Benchmark gap list", "45-120 minutes", "Solo", "External method"],
  "Strategic Risk Radar": ["Risk scan", "Connects sustainability maturity to emerging commercial and systemic risks.", "Risk register, trends and leadership concerns", "Risk radar", "30-60 minutes", "Team", "Guidance only"],
  "Competitive Sustainability Positioning Matrix": ["Market positioning", "Tests whether sustainability is a differentiator, requirement or risk in the market.", "Competitor evidence, customer expectations and strategic intent", "Positioning map", "45-90 minutes", "Team", "Downloadable guidance"],
  "Value Chain Mapping": ["Value-chain investigation", "Locates high-impact, high-risk and high-leverage points for later journey mapping.", "Process maps, suppliers, activities and flow data", "Value-chain stage map", "60-120 minutes", "Team", "Downloadable guidance"],
  "Flourishing Business Canvas": ["Business model design", "Tests whether value creation includes social and ecological outcomes.", "Business model, stakeholders, impacts and value exchanges", "Business model opportunity map", "90-180 minutes", "Facilitation recommended", "External method"],
  "Environmental Profit and Loss": ["Financial impact lens", "Translates environmental impacts into decision-relevant financial terms.", "Environmental data, activity volumes and valuation assumptions", "Environmental cost view", "90+ minutes", "Requires specialist", "External method"],
  "Monte Carlo Risk Analysis": ["Uncertainty model", "Shows how financial or risk assumptions behave under uncertainty.", "Financial model inputs, ranges and probability assumptions", "Risk distribution", "90+ minutes", "Requires specialist", "External method"]
};

const root = document.querySelector("[data-question-root]");
const form = document.querySelector("[data-explore-form]");
const storageKey = "greenSpectrum.explore.v1";
const onboardingKey = "greenSpectrum.onboarding.v1";
const saved = JSON.parse(localStorage.getItem(storageKey) || "{}");
const onboarding = JSON.parse(localStorage.getItem(onboardingKey) || "{}");
const state = { responses: saved.responses || {}, problemSignals: saved.problemSignals || [], intelligence: saved.intelligence || null };
const businessQuestions = questions.filter((item) => item.empathy === "business");
const humanQuestions = questions.filter((item) => item.empathy === "human");
const planetaryQuestions = questions.filter((item) => item.empathy === "planetary");
const activeQuestions = [...businessQuestions, ...humanQuestions, ...planetaryQuestions];

document.querySelector("[data-organisation-label]").textContent = onboarding.organisationName || "New journey";

renderQuestions();
restoreValues();
updateExplore();
restoreBackend();

function renderQuestions() {
  const themes = [...new Set(businessQuestions.map((item) => item.theme))];
  const humanThemes = [...new Set(humanQuestions.map((item) => item.theme))];
  const planetaryThemes = [...new Set(planetaryQuestions.map((item) => item.theme))];
  root.innerHTML = `
    <details class="onboarding-section empathy-section" id="business-empathy" data-empathy="business">
      <summary><span>01</span><b>${empathyMeta.business.title}</b><small>16 questions · complete or editable · <em data-empathy-state="business">Not started</em></small></summary>
      <div class="section-body">
        <p>${empathyMeta.business.copy}</p>
        <div class="investigation-depth-grid">
          <article><b>Quick review</b><span>15-20 minutes</span><p>Answer maturity, confidence and key evidence gaps.</p></article>
          <article><b>Standard investigation</b><span>25-45 minutes</span><p>Add discovery prompts, evidence cards and selected tools.</p></article>
          <article><b>Deep investigation</b><span>45+ minutes</span><p>Complete selected tools, gather stakeholder evidence and create formal handover outputs.</p></article>
        </div>
        <details class="micro-detail" open>
          <summary>Cross-cutting discovery paths</summary>
          <div class="domain-grid">${Object.entries(businessDiscoveryDomains).map(([domain, ids]) => `<article><b>${domain}</b><small>Questions ${ids.join(", ")}</small></article>`).join("")}</div>
        </details>
        ${themes.map((theme, themeIndex) => renderTheme(theme, businessQuestions.filter((item) => item.theme === theme), themeIndex === 0)).join("")}
      </div>
    </details>
    <details class="onboarding-section empathy-section" id="human-empathy" data-empathy="human">
      <summary><span>02</span><b>Human Empathy</b><small>5 questions · people, power and participation · <em data-empathy-state="human">Not started</em></small></summary>
      <div class="section-body">
        <div class="business-handover" data-business-handover>
          <p class="eyebrow">Business-to-Human handover</p>
          <h3>What should we investigate from a human perspective?</h3>
          <div data-handover-cards></div>
        </div>
        <div class="investigation-depth-grid">
          <article><b>Quick review</b><span>10-15 minutes</span><p>Answer maturity, representation and confidence.</p></article>
          <article><b>Standard investigation</b><span>20-40 minutes</span><p>Complete relevant prompts, link evidence and review tools.</p></article>
          <article><b>Deeper stakeholder work</b><span>Additional sessions</span><p>Create research tasks, prepare tools or plan facilitated activities.</p></article>
        </div>
        <details class="micro-detail" open>
          <summary>Human discovery domains</summary>
          <div class="domain-grid">${Object.entries(humanDiscoveryDomains).map(([domain, ids]) => `<article><b>${domain}</b><small>Questions ${ids.join(", ")}</small></article>`).join("")}</div>
        </details>
        ${humanThemes.map((theme, themeIndex) => renderTheme(theme, humanQuestions.filter((item) => item.theme === theme), themeIndex === 0)).join("")}
      </div>
    </details>
    <details class="onboarding-section empathy-section" id="planetary-empathy" data-empathy="planetary" open>
      <summary><span>03</span><b>Planetary Empathy</b><small>4 questions · ecological systems investigation · <em data-empathy-state="planetary">Not started</em></small></summary>
      <div class="section-body">
        <div class="business-handover" data-planetary-handover>
          <p class="eyebrow">Cross-empathy handover</p>
          <h3>What should we investigate from an ecological perspective?</h3>
          <div data-planetary-handover-cards></div>
        </div>
        <div class="investigation-depth-grid">
          <article><b>Quick review</b><span>10-15 minutes</span><p>Complete four maturity questions, confidence and major unknowns.</p></article>
          <article><b>Standard investigation</b><span>20-40 minutes</span><p>Add discovery prompts, evidence, boundaries and tool routing.</p></article>
          <article><b>Deep ecological work</b><span>Specialist sessions</span><p>Create evidence tasks for LCA, nature risk, material flow or resilience work.</p></article>
        </div>
        <details class="micro-detail" open>
          <summary>Planetary discovery domains</summary>
          <div class="domain-grid">${Object.entries(planetaryDiscoveryDomains).map(([domain, ids]) => `<article><b>${domain}</b><small>Questions ${ids.join(", ")}</small></article>`).join("")}</div>
        </details>
        ${planetaryThemes.map((theme, themeIndex) => renderTheme(theme, planetaryQuestions.filter((item) => item.theme === theme), themeIndex === 0)).join("")}
      </div>
    </details>
  ` + renderReviewAccordion();
}

function renderTheme(theme, items, open) {
  return `
    <details class="theme-section" ${open ? "open" : ""}>
      <summary><b>${theme}</b><small>${items.length} question${items.length > 1 ? "s" : ""}</small></summary>
      <div class="theme-body">${items.map(renderQuestion).join("")}</div>
    </details>
  `;
}

function renderQuestion(item) {
  const domains = domainsForQuestion(item.id);
  return `
    <article class="question-card" data-question="${item.id}">
      <div class="question-kicker">Question ${item.id} · ${titleCase(item.empathy)} Empathy · ${item.area}</div>
      <h3>${item.question}</h3>
      <details class="micro-detail" open><summary>Orientation and why this matters</summary><p>${whyItMatters(item)}</p><p><strong>Estimated time:</strong> ${item.id <= 6 ? "8-12 minutes" : "6-10 minutes"} if answered as a standard investigation.</p></details>
      <details class="micro-detail"><summary>${item.empathy === "planetary" ? "Imported Business and Human context" : item.empathy === "human" ? "Imported Business context" : "Imported context"}</summary><div class="context-grid">${item.empathy === "planetary" ? renderCrossEmpathyContextForPlanetary(item) : item.empathy === "human" ? renderBusinessContextForHuman(item) : renderImportedContext()}</div></details>
      <details class="micro-detail" open><summary>Discovery prompts and pathways</summary><div class="domain-grid">${domains.map((domain) => `<article><b>${domain}</b><small>Discovery path</small></article>`).join("")}</div><ul>${item.discovery.map((text) => `<li>${text}</li>`).join("")}</ul></details>
      <details class="micro-detail"><summary>Recommended investigation tools</summary><div class="tool-card-row">${item.tools.map((tool) => renderToolCard(tool, item)).join("")}</div></details>
      <details class="micro-detail"><summary>Evidence-source cards</summary><div class="evidence-card-row">${item.evidence.map((source) => renderEvidenceCard(source, item)).join("")}</div></details>
      ${item.empathy === "human" ? renderStakeholderRepresentation(item) : ""}
      ${item.empathy === "planetary" ? renderEcologicalBoundary(item) : ""}
      <fieldset>
        <legend>Select the maturity level that best reflects the current situation.</legend>
        <div class="maturity-options">
          ${maturityLevels.map(([value, label], levelIndex) => `
            <label class="select-card maturity-option ${value}">
              <input type="radio" name="q${item.id}-maturity" value="${value}">
              <span>${label}</span>
              <small>${value === "unknown" ? "There is not yet enough evidence to choose responsibly." : item.levels[levelIndex]}</small>
            </label>
          `).join("")}
        </div>
      </fieldset>
      <div class="form-grid">
        <label class="field-label">Evidence confidence
          <select name="q${item.id}-confidence">
            <option value="">Select confidence</option>
            <option value="high">High confidence</option>
            <option value="medium">Medium confidence</option>
            <option value="low">Low confidence</option>
            <option value="assumption">Assumption only</option>
            <option value="not_assessed">Not assessed</option>
          </select>
        </label>
        <label class="field-label">Answer scope
          <select name="q${item.id}-scope">
            <option value="">Select scope</option>
            <option>Whole organisation</option>
            <option>Business unit</option>
            <option>Region</option>
            <option>Site</option>
            <option>Product</option>
            <option>Service</option>
            <option>Value chain</option>
            <option>Department</option>
            <option>Mixed</option>
            <option>Unclear</option>
          </select>
        </label>
        <label class="field-label">Evidence references <input name="q${item.id}-evidence" type="text" placeholder="Report, dashboard, interview or file reference"></label>
        <label class="field-label full">Notes or supporting enquiry <textarea name="q${item.id}-notes" rows="3" placeholder="Add context, uncertainty or differences by department"></textarea></label>
      </div>
      <fieldset>
        <legend>${item.empathy === "human" ? "Relevant stakeholder groups" : "Stakeholder suggestions"}</legend>
        <div class="chip-grid">
          ${stakeholdersFor(item).map((group) => `<label><input type="checkbox" name="q${item.id}-stakeholders" value="${group}">${group}</label>`).join("")}
        </div>
      </fieldset>
      ${item.empathy === "human" ? `
        <fieldset>
          <legend>Behavioural, capability and participation signals</legend>
          <div class="form-grid">
            <label class="field-label">Behavioural barriers <input name="q${item.id}-barriers" type="text" placeholder="Incentives, trust, authority, skills, time, fatigue or habits"></label>
            <label class="field-label">Capability gaps <input name="q${item.id}-capabilityGaps" type="text" placeholder="Role-specific skills, learning, data or support gaps"></label>
            <label class="field-label">Power or influence concern <input name="q${item.id}-powerConcern" type="text" placeholder="High exposure, low influence, unclear authority or filtered evidence"></label>
            <label class="field-label">Stakeholder research task <input name="q${item.id}-researchTask" type="text" placeholder="Purpose, method or group to involve next"></label>
          </div>
        </fieldset>
        <fieldset>
          <legend>Sensitive human-risk check</legend>
          <div class="chip-grid">
            <label><input type="checkbox" name="q${item.id}-humanRisk" value="Safety concern">Safety concern</label>
            <label><input type="checkbox" name="q${item.id}-humanRisk" value="Safeguarding concern">Safeguarding concern</label>
            <label><input type="checkbox" name="q${item.id}-humanRisk" value="Severe labour concern">Severe labour concern</label>
            <label><input type="checkbox" name="q${item.id}-humanRisk" value="Human-rights concern">Human-rights concern</label>
          </div>
          <p class="inline-insight">Urgent human-risk notes stay separate from maturity scoring and should not be exported into general analytics.</p>
        </fieldset>
      ` : ""}
      ${item.empathy === "planetary" ? `
        <fieldset>
          <legend>Impact, dependency and environmental evidence</legend>
          <div class="form-grid">
            <label class="field-label">Ecological dependencies <input name="q${item.id}-dependencies" type="text" placeholder="Water, land, biodiversity, climate stability, suppliers, ecosystem services"></label>
            <label class="field-label">Impact signals <input name="q${item.id}-impactSignal" type="text" placeholder="Emissions, waste, pollution, land, water, biodiversity or material impacts"></label>
            <label class="field-label">Material flow signal <input name="q${item.id}-materialFlow" type="text" placeholder="Critical material, source, destination, circularity or toxicity concern"></label>
            <label class="field-label">Environmental evidence task <input name="q${item.id}-environmentalTask" type="text" placeholder="Evidence needed, owner, specialist or method"></label>
          </div>
        </fieldset>
        <fieldset>
          <legend>Planetary risk and quality flags</legend>
          <div class="chip-grid">
            <label><input type="checkbox" name="q${item.id}-planetaryRisk" value="Low evidence">Low evidence</label>
            <label><input type="checkbox" name="q${item.id}-planetaryRisk" value="Regenerative overclaim">Regenerative overclaim</label>
            <label><input type="checkbox" name="q${item.id}-planetaryRisk" value="Offset dependency">Offset dependency</label>
            <label><input type="checkbox" name="q${item.id}-planetaryRisk" value="Rebound effect">Rebound effect</label>
            <label><input type="checkbox" name="q${item.id}-planetaryRisk" value="Burden shifting">Burden shifting</label>
            <label><input type="checkbox" name="q${item.id}-planetaryRisk" value="Cascading ecological risk">Cascading ecological risk</label>
          </div>
        </fieldset>
      ` : ""}
      <fieldset>
        <legend>Strategic importance</legend>
        <div class="chip-grid">
          <label><input type="checkbox" name="q${item.id}-flags" value="Strategically important">Strategically important</label>
          <label><input type="checkbox" name="q${item.id}-flags" value="Regulatory priority">Regulatory priority</label>
          <label><input type="checkbox" name="q${item.id}-flags" value="High stakeholder concern">High stakeholder concern</label>
          <label><input type="checkbox" name="q${item.id}-flags" value="Immediate risk">Immediate risk</label>
          <label><input type="checkbox" name="q${item.id}-flags" value="Review later">Review later</label>
        </div>
      </fieldset>
      <details class="micro-detail"><summary>Reflection</summary>
        <div class="form-grid">
          <label class="field-label">What supports this judgement? <textarea name="q${item.id}-supports" rows="2" placeholder="Evidence, conversations, observations or reports"></textarea></label>
          <label class="field-label">What is uncertain? <textarea name="q${item.id}-uncertain" rows="2" placeholder="Unknowns, assumptions, weak data or contradictions"></textarea></label>
          <label class="field-label">What is most important? <textarea name="q${item.id}-important" rows="2" placeholder="The signal, risk or opportunity to remember"></textarea></label>
          <label class="field-label">What should be investigated later? <textarea name="q${item.id}-later" rows="2" placeholder="Questions for tools, Human Empathy or Impact Journey"></textarea></label>
        </div>
      </details>
      <fieldset>
        <legend>System connections</legend>
        <div class="chip-grid">${systemOptions.map((option) => `<label><input type="checkbox" name="q${item.id}-systems" value="${option}">${option}</label>`).join("")}</div>
      </fieldset>
      <fieldset>
        <legend>Carry forward</legend>
        <div class="chip-grid">${carryForwardOptions.map(([value, label]) => `<label><input type="checkbox" name="q${item.id}-carry" value="${value}">${label}</label>`).join("")}</div>
      </fieldset>
      <label class="field-label">Skip or review reason <input name="q${item.id}-skip" type="text" placeholder="Optional reason if skipped or marked for review"></label>
      <div class="inline-insight" data-interpretation="${item.id}">Select a maturity level and confidence rating to generate a provisional interpretation.</div>
      <button class="button button-primary" type="button" data-question-next="${item.id}">Save and continue</button>
    </article>
  `;
}

function renderReviewAccordion() {
  return `
    <details class="onboarding-section" data-empathy="review">
      <summary><span>04</span><b>Review and Synthesis</b><small>5–10 minutes · <em>Generated from responses</em></small></summary>
      <div class="section-body">
        <p>Use the synthesis section below to edit problem statements, review evidence gaps and confirm the profile is accurate enough to continue.</p>
        <a class="button button-secondary" href="#explore-synthesis">Open synthesis</a>
      </div>
    </details>
  `;
}

function domainsForQuestion(id) {
  const number = Number(id);
  const source = number >= 22 ? planetaryDiscoveryDomains : number >= 17 ? humanDiscoveryDomains : businessDiscoveryDomains;
  return Object.entries(source)
    .filter(([, ids]) => ids.includes(Number(id)))
    .map(([domain]) => domain);
}

function whyItMatters(item) {
  const copy = {
    1: "Strategy and purpose reveal whether sustainability is part of value creation or held separately as risk, reporting or reputation management.",
    2: "Governance shows whether sustainability has authority, accountability and influence over real decisions.",
    3: "Culture and engagement show whether people can translate ambition into day-to-day behaviour.",
    4: "Materiality and risk determine whether the organisation is seeing connected business, human and planetary consequences.",
    5: "Transparency and accountability test whether claims, reporting and decision evidence can be trusted.",
    6: "Metrics reveal whether the organisation measures outcomes that matter or only activities that are easy to count.",
    7: "Product and service innovation shows whether sustainability changes what the organisation offers, not just how it reports.",
    8: "Operations and circularity reveal high-impact, high-risk and high-leverage points for later journey mapping.",
    9: "Finance and investment show whether ambition is supported by budgets, capital allocation and risk pricing.",
    10: "Data and digital capability affects whether evidence can support decisions with confidence.",
    11: "Policy and regulation readiness shows whether the organisation is reacting to compliance or preparing for future requirements.",
    12: "Partnerships reveal where the organisation needs others to create systemic change.",
    13: "Innovation and R&D alignment show whether experimentation is aimed at sustainability outcomes.",
    14: "Learning and adaptation show whether the organisation can absorb feedback and change course.",
    15: "Crisis readiness and resilience reveal dependencies, shocks and adaptive capacity.",
    16: "Regenerative business identity tests whether the organisation is redefining its role in wider social and ecological systems.",
    17: "Stakeholder engagement reveals who shapes priorities, whose knowledge is heard and whether participation can influence decisions.",
    18: "Behavioural change and incentives reveal whether people have authority, support and motivation to act.",
    19: "Customer engagement tests whether customers have agency, credible information and realistic choices.",
    20: "Human and community wellbeing shows who experiences benefits, costs, harm or transition pressure.",
    21: "Equity, justice and inclusion reveal whether sustainability distributes power, value and harm fairly.",
    22: "Ecosystem stewardship reveals how the organisation affects and depends on habitats, ecosystem services, places and restoration outcomes.",
    23: "Value chain and traceability show where supplier origins, Scope 3 impacts and ecological dependencies remain visible or hidden.",
    24: "Circular design and materials reveal whether material flows, waste, recovery and burden shifting are understood.",
    25: "Climate and biodiversity integration checks whether climate, nature, finance and resilience are considered together."
  };
  return copy[item.id] || "This area helps reveal whether sustainability is influencing real decisions or remaining separate from day-to-day practice.";
}

function renderCrossEmpathyContextForPlanetary(item) {
  const completed = Object.values(state.responses).filter((response) => ["business", "human"].includes(response.empathy) && response.maturity);
  const candidates = completed.filter((response) => ["white", "light", "unknown"].includes(response.maturity) || response.needsReview).slice(0, 4);
  const sources = candidates.length ? candidates : completed.slice(0, 4);
  if (!sources.length) return `<article><b>Cross-empathy findings</b><p>No Business or Human findings are saved yet. Planetary Empathy can still proceed, but imported context will be limited.</p><small>Explore and Map · low confidence · reviewable</small></article>`;
  return sources.map((response) => `<article><b>${response.area}</b><p>${planetaryHandoverReason(response, item)}</p><small>${titleCase(response.empathy)} question ${response.id} · ${response.confidence || "unknown"} confidence · ${response.evidence ? "evidence linked" : "evidence gap"}</small></article>`).join("");
}

function planetaryHandoverReason(response, item) {
  if (item.id === 22) return `${response.area} may connect to ecosystem dependency, place-based impact or stewardship evidence.`;
  if (item.id === 23) return `${response.area} may require supplier, material-origin or value-chain traceability evidence.`;
  if (item.id === 24) return `${response.area} may reveal material-flow, recovery, waste or circularity trade-offs.`;
  return `${response.area} may connect climate, biodiversity, finance, resilience or unintended consequences.`;
}

function renderEcologicalBoundary(item) {
  return `
    <details class="micro-detail" open>
      <summary>Ecological and lifecycle boundary</summary>
      <div class="form-grid">
        <label class="field-label">Operational boundary
          <select name="q${item.id}-operationalBoundary">
            <option value="">Select boundary</option>
            <option>Whole organisation</option>
            <option>Site</option>
            <option>Product</option>
            <option>Service</option>
            <option>Project</option>
            <option>Supplier group</option>
            <option>Value-chain stage</option>
            <option>Geographic region</option>
            <option>Ecosystem</option>
            <option>Material</option>
            <option>Mixed</option>
            <option>Unclear</option>
          </select>
        </label>
        <label class="field-label">Lifecycle stages <input name="q${item.id}-lifecycleStages" type="text" placeholder="Raw materials, production, logistics, use, recovery, end of life"></label>
        <label class="field-label">Geography <input name="q${item.id}-geography" type="text" placeholder="Sites, regions, watersheds, supplier locations or markets"></label>
        <label class="field-label">Reporting period <input name="q${item.id}-reportingPeriod" type="text" placeholder="Year, baseline, latest study or unknown"></label>
        <label class="field-label">Included suppliers <input name="q${item.id}-includedSuppliers" type="text" placeholder="Tier, group or key suppliers included"></label>
        <label class="field-label">Known limitations <input name="q${item.id}-limitations" type="text" placeholder="Exclusions, proxies, data gaps or methodological limits"></label>
      </div>
    </details>
  `;
}

function renderBusinessContextForHuman(item) {
  const completedBusiness = Object.values(state.responses).filter((response) => response.empathy === "business" && response.maturity);
  const weak = completedBusiness.filter((response) => ["white", "light", "unknown"].includes(response.maturity) || response.needsReview).slice(0, 3);
  const sources = weak.length ? weak : completedBusiness.slice(0, 3);
  if (!sources.length) return `<article><b>Business findings</b><p>No Business findings are saved yet. Human Empathy can still proceed, but Business context will be limited.</p><small>Business Empathy · low confidence · reviewable</small></article>`;
  return sources.map((response) => `<article><b>${response.area}</b><p>${humanHandoverReason(response, item)}</p><small>Business question ${response.id} · ${response.confidence || "unknown"} confidence · ${response.evidence ? "evidence linked" : "evidence gap"}</small></article>`).join("");
}

function humanHandoverReason(response, item) {
  if (item.id === 17) return `${response.area} may need stakeholder influence, participation and voice checked before it becomes a Human conclusion.`;
  if (item.id === 18) return `${response.area} may depend on incentives, authority, behaviour or culture in practice.`;
  if (item.id === 19) return `${response.area} may affect customer agency, claims, choices or co-creation.`;
  if (item.id === 20) return `${response.area} may have worker, supplier or community wellbeing consequences.`;
  return `${response.area} may have equity, justice, accessibility or power-distribution implications.`;
}

function renderStakeholderRepresentation(item) {
  const groups = stakeholdersFor(item).slice(0, 6);
  return `
    <details class="micro-detail" open>
      <summary>Stakeholder representation and power check</summary>
      <div class="representation-grid">
        ${groups.map((group) => `
          <article class="representation-card">
            <b>${group}</b>
            <label>Representation
              <select name="q${item.id}-rep-${slugify(group)}">${representationStatuses.map((status) => `<option>${status}</option>`).join("")}</select>
            </label>
            <label>Influence
              <select name="q${item.id}-influence-${slugify(group)}">${influenceLevels.map((status) => `<option>${status}</option>`).join("")}</select>
            </label>
            <label>Impact exposure
              <select name="q${item.id}-exposure-${slugify(group)}">${impactExposureLevels.map((status) => `<option>${status}</option>`).join("")}</select>
            </label>
          </article>
        `).join("")}
      </div>
    </details>
  `;
}

function renderImportedContext() {
  const items = [
    ["Organisation", onboarding.organisationName || "Not provided", "Onboarding", "User supplied", "reviewable"],
    ["Industry", onboarding.industry || "Not provided", "Onboarding", "User supplied", "reviewable"],
    ["Journey mode", onboarding.mode || "Solo or facilitation mode not set", "Onboarding", "User supplied", "reviewable"],
    ["Data sources", Array.isArray(onboarding.dataSources) ? onboarding.dataSources.join(", ") : onboarding.dataSources || "Not provided", "Onboarding", "User supplied", "reviewable"],
    ["Known constraints", Array.isArray(onboarding.constraints) ? onboarding.constraints.join(", ") : onboarding.constraints || "Not provided", "Onboarding", "User supplied", "reviewable"]
  ];
  return items.map(([label, value, source, confidence, status]) => `<article><b>${label}</b><p>${escapeHtml(value)}</p><small>${source} · ${confidence} · ${status}</small></article>`).join("");
}

function renderToolCard(tool, item) {
  const details = toolDetails(tool);
  const key = slugify(tool);
  return `
    <article class="investigation-tool-card" data-tool="${key}">
      <div><b>${tool}</b><span>${details[0]}</span></div>
      <p>${details[1]}</p>
      <dl>
        <div><dt>Question</dt><dd>Q${item.id} ${item.area}</dd></div>
        <div><dt>Inputs</dt><dd>${details[2]}</dd></div>
        <div><dt>Output</dt><dd>${details[3]}</dd></div>
        <div><dt>Effort</dt><dd>${details[4]}</dd></div>
        <div><dt>Suitability</dt><dd>${details[5]}</dd></div>
        <div><dt>Status</dt><dd>${details[6]}</dd></div>
      </dl>
      <div class="mini-action-row">
        <label><input type="checkbox" name="q${item.id}-tools" value="${tool}"> Save for later</label>
        <button type="button" data-tool-focus="${key}">Learn more</button>
      </div>
    </article>
  `;
}

function toolDetails(tool) {
  if (toolDefaults[tool]) return toolDefaults[tool];
  if (tool.includes("Mapping") || tool.includes("Map")) return ["Mapping tool", "Makes relationships, flows, ownership or leverage points visible for this question.", "Current process, stakeholder or evidence knowledge", "Structured map for later stages", "45-90 minutes", "Solo or team", "Guidance only"];
  if (tool.includes("Assessment") || tool.includes("Diagnostic") || tool.includes("Audit")) return ["Diagnostic tool", "Tests the current position against a structured set of criteria.", "Policies, records, interviews and available performance data", "Gap analysis and review tasks", "45-120 minutes", "Solo or team", "Downloadable guidance"];
  if (tool.includes("Analysis") || tool.includes("Scorecard") || tool.includes("Dashboard")) return ["Analysis tool", "Helps interpret evidence and compare performance against targets or risks.", "Reliable data, metrics and decision context", "Analytical view and evidence gaps", "60-120 minutes", "Solo or specialist", "External method"];
  return ["Investigation tool", "Helps answer this maturity question with more evidence and less assumption.", "Relevant documents, data and stakeholder knowledge", "Evidence-informed output", "30-90 minutes", "Solo or team", "Guidance only"];
}

function renderEvidenceCard(source, item) {
  const owner = evidenceOwner(source);
  return `
    <article class="evidence-source-card">
      <b>${titleCase(source)}</b>
      <p>Useful for checking ${item.area.toLowerCase()} claims, implementation and decision evidence.</p>
      <dl>
        <div><dt>Owner</dt><dd>${owner}</dd></div>
        <div><dt>Format</dt><dd>Document, dashboard, interview or decision record</dd></div>
        <div><dt>Recency</dt><dd>Prefer current year or latest decision cycle</dd></div>
        <div><dt>Confidence</dt><dd>Formal records help, but adoption may still need stakeholder evidence</dd></div>
      </dl>
      <div class="mini-action-row">
        <label><input type="checkbox" name="q${item.id}-evidenceTasks" value="${source}"> Create evidence task</label>
      </div>
    </article>
  `;
}

function evidenceOwner(source) {
  if (/board|governance|committee|minutes/i.test(source)) return "Company Secretary or Governance";
  if (/finance|budget|capex|investment|cash|insurance|treasury/i.test(source)) return "Finance";
  if (/supplier|procurement|logistics|materials/i.test(source)) return "Procurement or Operations";
  if (/employee|training|culture|staff|performance/i.test(source)) return "People or HR";
  if (/data|dashboard|system|digital/i.test(source)) return "Data or Digital";
  if (/risk|legal|compliance|policy|regulation/i.test(source)) return "Risk, Legal or Compliance";
  if (/product|customer|design|service/i.test(source)) return "Product, Service or Commercial";
  return "Sustainability, Strategy or relevant evidence owner";
}

function stakeholdersFor(item) {
  if (item.empathy === "human") {
    const base = ["Executive leadership", "Employees", "People or HR"];
    if (item.id === 17) base.push("Board", "Suppliers", "Communities", "Nature or ecosystems");
    if (item.id === 18) base.push("Line managers", "Champions", "Resistors", "Learning teams");
    if (item.id === 19) base.push("Customers", "Vulnerable customers", "Product or service teams", "Marketing");
    if (item.id === 20) base.push("Contractors", "Supply-chain workers", "Communities", "Health and safety");
    if (item.id === 21) base.push("Underrepresented groups", "Accessibility users", "Procurement", "Communities");
    return [...new Set(base)];
  }
  const base = ["Executive leadership", "Sustainability", "Strategy"];
  if ([2, 4, 5, 11, 15].includes(item.id)) base.push("Board", "Risk or legal", "Regulators");
  if ([7, 8, 12].includes(item.id)) base.push("Operations", "Procurement", "Suppliers", "Customers");
  if ([9].includes(item.id)) base.push("Finance", "Investors");
  if ([3, 14].includes(item.id)) base.push("People or HR");
  if ([10].includes(item.id)) base.push("Data or digital");
  if ([16].includes(item.id)) base.push("Communities", "Nature or ecosystems");
  return [...new Set(base.concat(stakeholderOptions.slice(0, 3)))];
}

function restoreValues() {
  Object.entries(state.responses).forEach(([id, response]) => {
    const maturity = form.querySelector(`[name="q${id}-maturity"][value="${response.maturity}"]`);
    if (maturity) maturity.checked = true;
    const confidence = form.querySelector(`[name="q${id}-confidence"]`);
    const scope = form.querySelector(`[name="q${id}-scope"]`);
    const evidence = form.querySelector(`[name="q${id}-evidence"]`);
    const notes = form.querySelector(`[name="q${id}-notes"]`);
    const skip = form.querySelector(`[name="q${id}-skip"]`);
    if (confidence) confidence.value = response.confidence || "";
    if (scope) scope.value = response.scope || "";
    if (evidence) evidence.value = response.evidence || "";
    if (notes) notes.value = response.notes || "";
    if (skip) skip.value = response.skippedReason || "";
    (response.selectedTools || []).forEach((tool) => {
      const field = form.querySelector(`[name="q${id}-tools"][value="${CSS.escape(tool)}"]`);
      if (field) field.checked = true;
    });
    (response.evidenceTasks || []).forEach((source) => {
      const field = form.querySelector(`[name="q${id}-evidenceTasks"][value="${CSS.escape(source)}"]`);
      if (field) field.checked = true;
    });
    (response.stakeholderSuggestions || []).forEach((group) => {
      const field = form.querySelector(`[name="q${id}-stakeholders"][value="${CSS.escape(group)}"]`);
      if (field) field.checked = true;
    });
    (response.representedGroups || []).forEach((group) => {
      const field = form.querySelector(`[name="q${id}-stakeholders"][value="${CSS.escape(group)}"]`);
      if (field) field.checked = true;
    });
    (response.humanRiskFlags || []).forEach((risk) => {
      const field = form.querySelector(`[name="q${id}-humanRisk"][value="${CSS.escape(risk)}"]`);
      if (field) field.checked = true;
    });
    ["barriers", "capabilityGaps", "powerConcern", "researchTask"].forEach((key) => {
      const field = form.querySelector(`[name="q${id}-${key}"]`);
      if (field) field.value = response[key] || "";
    });
    ["dependencies", "impactSignal", "materialFlow", "environmentalTask"].forEach((key) => {
      const field = form.querySelector(`[name="q${id}-${key}"]`);
      if (field) field.value = response[key] || "";
    });
    const boundary = response.ecologicalBoundary || {};
    ["operationalBoundary", "lifecycleStages", "geography", "reportingPeriod", "includedSuppliers", "limitations"].forEach((key) => {
      const field = form.querySelector(`[name="q${id}-${key}"]`);
      if (field) field.value = boundary[key] || "";
    });
    (response.planetaryRiskFlags || []).forEach((risk) => {
      const field = form.querySelector(`[name="q${id}-planetaryRisk"][value="${CSS.escape(risk)}"]`);
      if (field) field.checked = true;
    });
    (response.stakeholderRepresentation || []).forEach((entry) => {
      const key = slugify(entry.stakeholder || "");
      const rep = form.querySelector(`[name="q${id}-rep-${key}"]`);
      const influence = form.querySelector(`[name="q${id}-influence-${key}"]`);
      const exposure = form.querySelector(`[name="q${id}-exposure-${key}"]`);
      if (rep) rep.value = entry.representationStatus || "Unclear";
      if (influence) influence.value = entry.influenceLevel || "Unclear";
      if (exposure) exposure.value = entry.impactExposure || "Unclear";
    });
    (response.systemsConnections || []).forEach((connection) => {
      const field = form.querySelector(`[name="q${id}-systems"][value="${CSS.escape(connection)}"]`);
      if (field) field.checked = true;
    });
    (response.carryForwardActions || []).forEach((action) => {
      const field = form.querySelector(`[name="q${id}-carry"][value="${CSS.escape(action)}"]`);
      if (field) field.checked = true;
    });
    const reflection = response.reflection || {};
    ["supports", "uncertain", "important", "later"].forEach((key) => {
      const field = form.querySelector(`[name="q${id}-${key}"]`);
      if (field) field.value = reflection[key] || "";
    });
    (response.flags || []).forEach((flag) => {
      const field = form.querySelector(`[name="q${id}-flags"][value="${CSS.escape(flag)}"]`);
      if (field) field.checked = true;
    });
  });
}

function getResponse(id) {
  const item = questions.find((question) => question.id === Number(id));
  return {
    id: Number(id),
    empathy: item.empathy,
    area: item.area,
    maturity: form.querySelector(`[name="q${id}-maturity"]:checked`)?.value || "",
    confidence: form.querySelector(`[name="q${id}-confidence"]`)?.value || "",
    scope: form.querySelector(`[name="q${id}-scope"]`)?.value || "",
    evidence: form.querySelector(`[name="q${id}-evidence"]`)?.value || "",
    notes: form.querySelector(`[name="q${id}-notes"]`)?.value || "",
    flags: [...form.querySelectorAll(`[name="q${id}-flags"]:checked`)].map((field) => field.value),
    discoveryDomains: domainsForQuestion(item.id),
    selectedTools: [...form.querySelectorAll(`[name="q${id}-tools"]:checked`)].map((field) => field.value),
    evidenceTasks: [...form.querySelectorAll(`[name="q${id}-evidenceTasks"]:checked`)].map((field) => field.value),
    stakeholderSuggestions: [...form.querySelectorAll(`[name="q${id}-stakeholders"]:checked`)].map((field) => field.value),
    representedGroups: [...form.querySelectorAll(`[name="q${id}-stakeholders"]:checked`)].map((field) => field.value),
    underrepresentedGroups: item.empathy === "human" ? stakeholdersFor(item).filter((group) => {
      const key = slugify(group);
      const rep = form.querySelector(`[name="q${id}-rep-${key}"]`)?.value || "";
      return rep === "Not represented" || rep === "Unclear";
    }) : [],
    stakeholderRepresentation: item.empathy === "human" ? stakeholdersFor(item).slice(0, 6).map((group) => {
      const key = slugify(group);
      return {
        stakeholder: group,
        role: group,
        representationStatus: form.querySelector(`[name="q${id}-rep-${key}"]`)?.value || "Unclear",
        influenceLevel: form.querySelector(`[name="q${id}-influence-${key}"]`)?.value || "Unclear",
        impactExposure: form.querySelector(`[name="q${id}-exposure-${key}"]`)?.value || "Unclear",
        decisionAuthority: form.querySelector(`[name="q${id}-influence-${key}"]`)?.value || "Unclear",
        evidenceType: form.querySelector(`[name="q${id}-rep-${key}"]`)?.value || "Unclear",
        confidentialityLevel: "Group-level"
      };
    }) : [],
    systemsConnections: [...form.querySelectorAll(`[name="q${id}-systems"]:checked`)].map((field) => field.value),
    carryForwardActions: [...form.querySelectorAll(`[name="q${id}-carry"]:checked`)].map((field) => field.value),
    barriers: form.querySelector(`[name="q${id}-barriers"]`)?.value || "",
    capabilityGaps: form.querySelector(`[name="q${id}-capabilityGaps"]`)?.value || "",
    powerConcern: form.querySelector(`[name="q${id}-powerConcern"]`)?.value || "",
    researchTask: form.querySelector(`[name="q${id}-researchTask"]`)?.value || "",
    humanRiskFlags: [...form.querySelectorAll(`[name="q${id}-humanRisk"]:checked`)].map((field) => field.value),
    ecologicalBoundary: item.empathy === "planetary" ? {
      organisationalScope: form.querySelector(`[name="q${id}-operationalBoundary"]`)?.value || "",
      operationalBoundary: form.querySelector(`[name="q${id}-operationalBoundary"]`)?.value || "",
      lifecycleStages: form.querySelector(`[name="q${id}-lifecycleStages"]`)?.value || "",
      geography: form.querySelector(`[name="q${id}-geography"]`)?.value || "",
      geographicScope: form.querySelector(`[name="q${id}-geography"]`)?.value || "",
      reportingPeriod: form.querySelector(`[name="q${id}-reportingPeriod"]`)?.value || "",
      includedSuppliers: form.querySelector(`[name="q${id}-includedSuppliers"]`)?.value || "",
      limitations: form.querySelector(`[name="q${id}-limitations"]`)?.value || ""
    } : {},
    dependencies: form.querySelector(`[name="q${id}-dependencies"]`)?.value || "",
    impactSignal: form.querySelector(`[name="q${id}-impactSignal"]`)?.value || "",
    materialFlow: form.querySelector(`[name="q${id}-materialFlow"]`)?.value || "",
    environmentalTask: form.querySelector(`[name="q${id}-environmentalTask"]`)?.value || "",
    planetaryRiskFlags: [...form.querySelectorAll(`[name="q${id}-planetaryRisk"]:checked`)].map((field) => field.value),
    reflection: {
      supports: form.querySelector(`[name="q${id}-supports"]`)?.value || "",
      uncertain: form.querySelector(`[name="q${id}-uncertain"]`)?.value || "",
      important: form.querySelector(`[name="q${id}-important"]`)?.value || "",
      later: form.querySelector(`[name="q${id}-later"]`)?.value || ""
    },
    toolRecommendations: item.tools.map((tool) => ({ tool, questionId: item.id, questionArea: item.area, reason: toolDetails(tool)[1], output: toolDetails(tool)[3], availability: toolDetails(tool)[6] })),
    skippedReason: form.querySelector(`[name="q${id}-skip"]`)?.value || "",
    slug: slugify(item.area),
    needsReview: Boolean(form.querySelector(`[name="q${id}-skip"]`)?.value || ["low", "assumption", "not_assessed"].includes(form.querySelector(`[name="q${id}-confidence"]`)?.value || "")),
    interpretation: document.querySelector(`[data-interpretation="${id}"]`)?.textContent || "",
    updatedAt: new Date().toISOString()
  };
}

function completedResponses() {
  return Object.values(state.responses).filter((response) => response.maturity && response.confidence);
}

function updateExplore() {
  activeQuestions.forEach((item) => {
    state.responses[item.id] = getResponse(item.id);
    const interpretation = document.querySelector(`[data-interpretation="${item.id}"]`);
    if (interpretation) interpretation.textContent = interpret(item, state.responses[item.id]);
  });
  const completed = completedResponses();
  const businessCompleted = completed.filter((item) => item.empathy === "business");
  const humanCompleted = completed.filter((item) => item.empathy === "human");
  const planetaryCompleted = completed.filter((item) => item.empathy === "planetary");
  const boundaryRecords = planetaryCompleted.filter((item) => item.ecologicalBoundary?.operationalBoundary || item.ecologicalBoundary?.geography || item.ecologicalBoundary?.lifecycleStages).length;
  const evidenceLinked = planetaryCompleted.filter((item) => item.evidence).length;
  const environmentalTasks = planetaryCompleted.filter((item) => item.environmentalTask || item.maturity === "unknown").length;
  const lowConfidence = planetaryCompleted.filter((item) => ["low", "assumption", "not_assessed"].includes(item.confidence)).length;
  const needsReview = planetaryCompleted.filter((item) => item.needsReview || item.maturity === "unknown" || (item.planetaryRiskFlags || []).length).length;
  const percent = Math.round((planetaryCompleted.length / planetaryQuestions.length) * 100);
  setText("[data-question-progress]", `${planetaryCompleted.length} of 4 Planetary questions answered`);
  setText("[data-empathy-progress]", `${boundaryRecords} boundary records · ${evidenceLinked} evidence-linked answers · ${environmentalTasks} evidence tasks · ${lowConfidence} low-confidence responses · ${needsReview} need review`);
  setText("[data-time-remaining]", `Approximately ${Math.max(5, 20 - planetaryCompleted.length * 4)} minutes remaining`);
  const fill = document.querySelector("[data-explore-progress-fill]");
  if (fill) fill.style.width = `${percent}%`;
  const target = document.querySelector('[data-empathy-state="business"]');
  if (target) target.textContent = businessCompleted.length === businessQuestions.length ? "Complete" : businessCompleted.length ? `${businessCompleted.length} of 16` : "Not started";
  const humanTarget = document.querySelector('[data-empathy-state="human"]');
  if (humanTarget) humanTarget.textContent = humanCompleted.length === humanQuestions.length ? "Complete" : humanCompleted.length ? `${humanCompleted.length} of 5` : "Not started";
  const planetaryTarget = document.querySelector('[data-empathy-state="planetary"]');
  if (planetaryTarget) planetaryTarget.textContent = planetaryCompleted.length === planetaryQuestions.length ? "Complete" : planetaryCompleted.length ? `${planetaryCompleted.length} of 4` : "Not started";
  renderBusinessHandover();
  renderPlanetaryHandover();
  state.intelligence = buildClientIntelligence(completedResponses().filter((item) => ["business", "human", "planetary"].includes(item.empathy)));
  updateSummaryPanel();
  updateSynthesis();
  renderIntelligencePanel(state.intelligence);
  save();
}

function empathyPercent(empathy) {
  const total = activeQuestions.filter((item) => item.empathy === empathy).length || 1;
  const done = completedResponses().filter((item) => item.empathy === empathy).length;
  return Math.round((done / total) * 100);
}

function interpret(item, response) {
  if (!response.maturity || !response.confidence) return "Select a maturity level and confidence rating to generate a provisional interpretation.";
  if (response.maturity === "unknown") return `${item.area} is currently an evidence gap. Treat this as a useful uncertainty rather than a failure.`;
  const level = maturityLevels.find(([value]) => value === response.maturity)?.[1];
  return `${item.area} is provisionally marked as ${level} with ${response.confidence} confidence. Use notes to capture departmental variation or uncertainty.`;
}

function updateSummaryPanel() {
  const completed = completedResponses();
  const unknown = completed.filter((item) => item.maturity === "unknown").length;
  const low = completed.filter((item) => ["low", "assumption"].includes(item.confidence)).length;
  const darkMid = completed.filter((item) => ["mid", "dark"].includes(item.maturity)).map((item) => item.area);
  const whiteLight = completed.filter((item) => ["white", "light"].includes(item.maturity)).map((item) => item.area);
  const summary = document.querySelector("[data-explore-summary]");
  if (summary) {
    summary.innerHTML = [
      ["Current maturity pattern", completed.length ? dominantLevel(completed) : "Missing"],
      ["Current strengths", darkMid.slice(0, 3).join(", ") || "Not enough evidence yet"],
      ["Potential hotspots", whiteLight.slice(0, 3).join(", ") || "Not enough evidence yet"],
      ["Evidence gaps", `${unknown + low} areas need review`],
      ["Questions to revisit", completed.filter((item) => item.maturity === "unknown").slice(0, 3).map((item) => item.area).join(", ") || "None yet"]
    ].map(([label, value]) => `<div class="summary-row"><dt>${label}</dt><dd>${value}</dd></div>`).join("");
  }
  const insight = document.querySelector("[data-explore-insight] p");
  if (insight) {
    insight.textContent = whiteLight.length
      ? `${whiteLight[0]} may be an early problem signal. This is based on selected maturity levels and should be checked against evidence.`
      : completed.length
        ? "No clear hotspot has emerged yet. Continue answering across all three empathies to reveal contradictions."
        : "Answer maturity and confidence questions to reveal strengths, hotspots and evidence gaps.";
  }
}

function updateSynthesis() {
  const completed = completedResponses().filter((item) => item.empathy === "business" || item.empathy === "human");
  list("[data-strengths]", completed.filter((item) => ["mid", "dark"].includes(item.maturity)).map((item) => `${item.area} (${item.empathy})`), "No strengths identified yet.");
  list("[data-hotspots]", completed.filter((item) => ["white", "light"].includes(item.maturity)).map((item) => `${item.area} (${item.empathy})`), "No hotspots identified yet.");
  list("[data-evidence-gaps]", completed.filter((item) => item.maturity === "unknown" || ["low", "assumption"].includes(item.confidence)).map((item) => `${item.area}: ${item.maturity === "unknown" ? "Not known" : item.confidence + " confidence"}`), "No evidence gaps identified yet.");
  list("[data-contradictions]", contradictions(completed), "Contradictions will appear as patterns emerge.");
  renderHeatmap();
  renderBars();
  renderProblemSignals();
  list("[data-impact-questions]", impactQuestions(completed), "Business problem signals will generate handover questions here.");
  list("[data-human-recommendations]", planetaryRecommendations(completed), "Planetary recommendations will appear once Human answers are saved.");
}

function renderHeatmap() {
  const heatmap = document.querySelector("[data-heatmap]");
  if (!heatmap) return;
  heatmap.innerHTML = activeQuestions.map((item) => {
    const response = state.responses[item.id] || {};
    return `<span class="${response.maturity || "empty"}" title="Question ${item.id}: ${item.area}">${item.id}</span>`;
  }).join("");
}

function renderBars() {
  const bars = document.querySelector("[data-profile-bars]");
  if (!bars) return;
  const businessPercent = empathyPercent("business");
  const completed = completedResponses();
  bars.innerHTML = `
    <div><b>Business Empathy</b><span><i style="width:${businessPercent}%"></i></span><small>${businessPercent}% complete · average ${businessAverage(completed.filter((item) => item.empathy === "business"))}</small></div>
    <div><b>Human Empathy</b><span><i style="width:${empathyPercent("human")}%"></i></span><small>${empathyPercent("human")}% complete · average ${businessAverage(completed.filter((item) => item.empathy === "human"))}</small></div>
  `;
}

function renderProblemSignals() {
  const completed = completedResponses();
  const generated = completed
    .filter((item) => ["white", "light", "unknown"].includes(item.maturity))
    .slice(0, 5)
    .map((item, index) => ({
      id: `signal-${item.id}`,
      title: `${item.area} may need deeper mapping`,
      description: `${item.area} is marked as ${item.maturity}. Review related evidence before deciding on interventions.`,
      source: `Question ${item.id}`,
      confidence: item.confidence || "low"
    }));
  const all = [...generated, ...state.problemSignals];
  const target = document.querySelector("[data-problem-signals]");
  if (!target) return;
  target.innerHTML = all.length ? all.map((signal) => `
    <article class="problem-signal">
      <label>Problem signal <input value="${escapeAttr(signal.title)}"></label>
      <textarea rows="2">${escapeHtml(signal.description)}</textarea>
      <small>${signal.source || "User added"} · ${signal.confidence} confidence</small>
    </article>
  `).join("") : "<p>No problem signals yet. Low maturity, Not known and low-confidence answers will generate editable signals.</p>";
}

function contradictions(completed) {
  const byArea = Object.fromEntries(completed.map((item) => [item.area, item.maturity]));
  const items = [];
  if (["mid", "dark"].includes(byArea["Governance and Leadership"]) && ["white", "light"].includes(byArea["Operations and Circularity"])) items.push("Governance appears more mature than operational implementation.");
  if (["mid", "dark"].includes(byArea["Strategy and Purpose"]) && ["white", "light"].includes(byArea["Finance and Investment"])) items.push("Strategic ambition may not yet be matched by financial alignment.");
  if (["mid", "dark"].includes(byArea["Customer Engagement"]) && ["white", "light"].includes(byArea["Value Chain and Traceability"])) items.push("Customer communication may be stronger than traceability evidence.");
  return items;
}

function complexityFlag(completed) {
  const lowEvidence = completed.filter((item) => ["low", "assumption"].includes(item.confidence) || item.maturity === "unknown").length;
  const hotspots = completed.filter((item) => ["white", "light"].includes(item.maturity)).length;
  if (!completed.length) return "Final complexity classification occurs later during Sort and Prioritise.";
  if (lowEvidence > 6) return "Provisional flag: unclear. Evidence gaps should be mapped before classifying complexity.";
  if (hotspots > 8) return "Provisional flag: likely complex. Multiple low-maturity areas may interact.";
  if (hotspots > 3) return "Provisional flag: likely complicated. Several areas need structured investigation.";
  return "Provisional flag: likely clear or complicated. Confirm later during Sort and Prioritise.";
}

function impactQuestions(completed) {
  return completed
    .filter((item) => ["white", "light", "unknown"].includes(item.maturity))
    .slice(0, 5)
    .map((item) => `Where does ${item.area.toLowerCase()} show up across the value chain, service journey or decision process?`);
}

function humanRecommendations(completed) {
  const areas = completed.filter((item) => ["white", "light", "unknown"].includes(item.maturity)).map((item) => item.area);
  const recommendations = [];
  if (areas.includes("Culture and Engagement") || areas.includes("Governance and Leadership")) recommendations.push("Explore ownership, incentives and behavioural barriers early in Human Empathy.");
  if (areas.includes("Transparency and Accountability")) recommendations.push("Check trust, representation and who can challenge the organisation's evidence.");
  if (areas.includes("Learning and Adaptation")) recommendations.push("Explore capability, psychological safety and how lessons are shared.");
  return recommendations.length ? recommendations : ["Use Human Empathy to test whether business maturity is experienced consistently by people and stakeholders."];
}

function buildClientIntelligence(business) {
  const nodes = [{ id: "organisation", type: "Organisation", title: onboarding.organisationName || "Organisation" }];
  const relationships = [];
  const capabilityMap = {
    "Strategy and Purpose": ["Strategy", "Purpose"],
    "Governance and Leadership": ["Governance", "Leadership"],
    "Culture and Engagement": ["Culture", "People", "Skills"],
    "Materiality and Risk": ["Risk", "Strategy"],
    "Transparency and Accountability": ["Reporting", "Governance"],
    "Metrics and Impact": ["Reporting", "Data"],
    "Product and Service Innovation": ["Innovation", "Customer"],
    "Operations and Circularity": ["Operations", "Supply Chain", "Circularity"],
    "Finance and Investment": ["Finance"],
    "Data and Digital": ["Data", "Technology"],
    "Policy and Regulation": ["Policy"],
    "Collaboration and Partnerships": ["Collaboration"],
    "Innovation and R&D Alignment": ["Innovation"],
    "Learning and Adaptation": ["Learning", "Skills"],
    "Crisis Readiness and Resilience": ["Resilience", "Risk"],
    "Regenerative Business Identity": ["Purpose", "Strategy"]
  };
  const buckets = {};
  const uncertainty = { unknownInformation: [], assumptions: [], missingEvidence: [], lowConfidence: [], conflictingEvidence: [] };
  business.forEach((item) => {
    nodes.push({ id: `q${item.id}`, type: "Answer", title: item.area });
    relationships.push({ id: `org-q${item.id}`, sourceNodeId: "organisation", targetNodeId: `q${item.id}`, type: "contains", evidence: item.evidence || "User response", confidence: item.confidence || "not_assessed" });
    if (item.evidence) {
      nodes.push({ id: `evidence-q${item.id}`, type: "Evidence", title: item.evidence });
      relationships.push({ id: `q${item.id}-evidence`, sourceNodeId: `q${item.id}`, targetNodeId: `evidence-q${item.id}`, type: "supported by", evidence: item.evidence, confidence: item.confidence || "not_assessed" });
    }
    (capabilityMap[item.area] || [item.area]).forEach((capability) => {
      buckets[capability] = buckets[capability] || [];
      buckets[capability].push(item);
      relationships.push({ id: `q${item.id}-${slugify(capability)}`, sourceNodeId: `q${item.id}`, targetNodeId: `capability-${slugify(capability)}`, type: "influences", evidence: item.area, confidence: item.confidence || "not_assessed" });
    });
    (item.systemsConnections || []).forEach((connection) => relationships.push({ id: `q${item.id}-${slugify(connection)}`, sourceNodeId: `q${item.id}`, targetNodeId: `system-${slugify(connection)}`, type: "connects to", evidence: item.area, confidence: item.confidence || "not_assessed" }));
    if (item.maturity === "unknown") uncertainty.unknownInformation.push(item.area);
    if (item.confidence === "assumption") uncertainty.assumptions.push(item.area);
    if (!item.evidence) uncertainty.missingEvidence.push(item.area);
    if (["low", "assumption", "not_assessed", ""].includes(item.confidence)) uncertainty.lowConfidence.push(item.area);
  });
  const capabilities = Object.entries(buckets).map(([capability, items]) => {
    const scoreMap = { white: 0, light: 1, mid: 2, dark: 3 };
    const scores = items.map((item) => scoreMap[item.maturity]).filter((score) => typeof score === "number");
    const average = scores.length ? scores.reduce((sum, score) => sum + score, 0) / scores.length : null;
    return {
      capability,
      currentMaturity: average === null ? "unknown" : average < 0.75 ? "white" : average < 1.5 ? "light" : average < 2.4 ? "mid" : "dark",
      maturityScore: average === null ? null : Math.round(average * 100) / 100,
      confidence: items.some((item) => ["low", "assumption", "not_assessed", ""].includes(item.confidence)) ? "low" : "medium",
      knownStrengths: items.filter((item) => ["mid", "dark"].includes(item.maturity)).map((item) => item.area),
      knownWeaknesses: items.filter((item) => ["white", "light"].includes(item.maturity)).map((item) => item.area),
      unknowns: items.filter((item) => item.maturity === "unknown" || !item.evidence).map((item) => item.area)
    };
  });
  const themes = clientThemes(business);
  const patterns = clientPatterns(business);
  const insights = patterns.length ? [{ title: patterns[0].title, explanation: patterns[0].explanation, confidence: patterns[0].confidence, supportingQuestions: patterns[0].supportingQuestions }] : [];
  return { graph: { nodes, relationships }, capabilities, themes, patterns, insights, uncertainty, latestInsight: insights[0] || null, latestRelationship: relationships[relationships.length - 1] || null };
}

function clientThemes(business) {
  const rules = [
    ["Governance", "Ownership Gap", ["Governance and Leadership", "Culture and Engagement", "Collaboration and Partnerships"]],
    ["Data", "Data Capability Gap", ["Metrics and Impact", "Data and Digital", "Transparency and Accountability"]],
    ["Finance", "Financial Alignment Gap", ["Finance and Investment", "Strategy and Purpose", "Innovation and R&D Alignment"]],
    ["Operations", "Operational Implementation Gap", ["Operations and Circularity", "Materiality and Risk", "Product and Service Innovation"]],
    ["Resilience", "Resilience Readiness Gap", ["Crisis Readiness and Resilience", "Policy and Regulation", "Materiality and Risk"]]
  ];
  return rules.flatMap(([type, title, areas]) => {
    const supporting = business.filter((item) => areas.includes(item.area) && (["white", "light", "unknown"].includes(item.maturity) || ["low", "assumption", "not_assessed", ""].includes(item.confidence)));
    return supporting.length >= 2 ? [{ type, title, description: `${supporting.length} related answers suggest a repeated ${type.toLowerCase()} pattern.`, supportingQuestions: supporting.map((item) => item.id), confidence: supporting.length > 2 ? "medium" : "low" }] : [];
  });
}

function clientPatterns(business) {
  const byArea = Object.fromEntries(business.map((item) => [item.area, item.maturity]));
  const patterns = [];
  if (["mid", "dark"].includes(byArea["Strategy and Purpose"]) && ["white", "light", "unknown"].includes(byArea["Finance and Investment"])) patterns.push({ title: "Strong strategy, weak finance", explanation: "Strategic ambition appears stronger than the financial mechanisms needed for implementation.", supportingQuestions: [1, 9], confidence: "medium" });
  if ((["mid", "dark"].includes(byArea["Transparency and Accountability"]) || ["mid", "dark"].includes(byArea["Metrics and Impact"])) && ["white", "light", "unknown"].includes(byArea["Operations and Circularity"])) patterns.push({ title: "Good reporting, weak implementation", explanation: "Transparency or metrics appear more mature than operational sustainability.", supportingQuestions: [5, 6, 8], confidence: "medium" });
  const confidentWithoutEvidence = business.filter((item) => ["high", "medium"].includes(item.confidence) && !item.evidence);
  if (confidentWithoutEvidence.length) patterns.push({ title: "High confidence, little evidence", explanation: "Some answers are confident but lack explicit evidence references.", supportingQuestions: confidentWithoutEvidence.map((item) => item.id), confidence: "low" });
  return patterns;
}

function renderIntelligencePanel(model) {
  if (!model) return;
  setText("[data-graph-node-count]", model.graph?.nodes?.length || 0);
  setText("[data-graph-relationship-count]", model.graph?.relationships?.length || 0);
  setText("[data-theme-count]", model.themes?.length || 0);
  list("[data-intelligence-themes]", (model.themes || []).slice(0, 4).map((theme) => `${theme.title}: ${theme.description}`), "Business answers will generate themes here.");
  list("[data-intelligence-capabilities]", (model.capabilities || []).slice(0, 5).map((capability) => `${capability.capability}: ${titleCase(capability.currentMaturity || "unknown")} maturity · ${capability.confidence} confidence`), "Capability profile will update as answers are saved.");
  list("[data-intelligence-patterns]", (model.patterns || []).map((pattern) => `${pattern.title}: ${pattern.explanation}`), "Patterns will appear as answers connect.");
  const uncertaintyItems = [
    ...(model.uncertainty?.unknownInformation || []).slice(0, 3).map((area) => `Unknown: ${area}`),
    ...(model.uncertainty?.missingEvidence || []).slice(0, 3).map((area) => `Missing evidence: ${area}`),
    ...(model.uncertainty?.assumptions || []).slice(0, 3).map((area) => `Assumption: ${area}`)
  ];
  list("[data-uncertainty-model]", uncertaintyItems, "Unknowns and assumptions will appear here.");
  const latest = model.latestRelationship;
  setText("[data-latest-relationship]", latest ? `${latest.sourceNodeId || "Answer"} ${latest.type || "relates to"} ${latest.targetNodeId || "model"} · ${latest.confidence || "unknown"} confidence` : "No system relationship yet.");
}

function planetaryRecommendations(completed) {
  const humanWeak = completed.filter((item) => item.empathy === "human" && ["white", "light", "unknown"].includes(item.maturity)).map((item) => item.area);
  const recommendations = [];
  if (humanWeak.includes("Human and Community Wellbeing") || humanWeak.includes("Equity, Justice and Inclusion")) recommendations.push("Check whether environmental impacts affect communities, workers or places unevenly.");
  if (humanWeak.includes("Customer Engagement")) recommendations.push("Explore product, material and use-phase impacts alongside customer agency.");
  if (humanWeak.includes("Stakeholder Engagement")) recommendations.push("Map ecological stakeholders and place-based dependencies with care.");
  return recommendations.length ? recommendations : ["Use Planetary Empathy to connect human findings to climate, nature, materials and ecological dependencies."];
}

function renderBusinessHandover() {
  const target = document.querySelector("[data-handover-cards]");
  if (!target) return;
  const completed = completedResponses().filter((item) => item.empathy === "business");
  const candidates = completed
    .filter((item) => ["white", "light", "unknown"].includes(item.maturity) || item.needsReview)
    .slice(0, 5);
  target.innerHTML = candidates.length ? candidates.map((item) => `
    <article class="handover-card">
      <h4>${item.area}</h4>
      <p>Imported from Business question ${item.id}. Human Empathy should test ownership, influence, trust or capability around this finding.</p>
      <small>${item.confidence || "unknown"} confidence · ${item.evidence ? "evidence linked" : "evidence gap"}</small>
    </article>
  `).join("") : "<p>No Business handover signals yet. Complete Business questions or continue with the default Human sequence.</p>";
}

function renderPlanetaryHandover() {
  const target = document.querySelector("[data-planetary-handover-cards]");
  if (!target) return;
  const completed = completedResponses().filter((item) => ["business", "human"].includes(item.empathy));
  const candidates = completed
    .filter((item) => ["white", "light", "unknown"].includes(item.maturity) || item.needsReview || item.area.includes("Operations") || item.area.includes("Wellbeing") || item.area.includes("Traceability"))
    .slice(0, 6);
  target.innerHTML = candidates.length ? candidates.map((item) => `
    <article class="handover-card">
      <h4>${item.area}</h4>
      <p>Imported from ${item.empathy} question ${item.id}. Planetary Empathy should check ecological impacts, dependencies, boundaries or environmental evidence around this finding.</p>
      <small>${item.confidence || "unknown"} confidence · ${item.evidence ? "evidence linked" : "evidence gap"}</small>
    </article>
  `).join("") : "<p>No cross-empathy handover signals yet. Planetary Empathy can proceed, but imported context will be limited.</p>";
}

function businessAverage(completed) {
  const scores = { white: 0, light: 1, mid: 2, dark: 3 };
  const scored = completed.map((item) => scores[item.maturity]).filter((score) => typeof score === "number");
  if (!scored.length) return "not enough evidence";
  const average = scored.reduce((sum, score) => sum + score, 0) / scored.length;
  if (average < 0.75) return "White";
  if (average < 1.5) return "Light Green";
  if (average < 2.4) return "Mid Green";
  return "Dark Green";
}

function dominantLevel(items) {
  const counts = {};
  items.forEach((item) => counts[item.maturity] = (counts[item.maturity] || 0) + 1);
  const dominant = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0];
  return maturityLevels.find(([value]) => value === dominant)?.[1] || "Mixed";
}

function list(selector, items, fallback) {
  const target = document.querySelector(selector);
  if (!target) return;
  target.innerHTML = items.length ? items.map((item) => `<li>${item}</li>`).join("") : `<li>${fallback}</li>`;
}

function save() {
  clearTimeout(save.timer);
  const autosave = document.querySelector("[data-explore-autosave]");
  if (autosave) autosave.textContent = "Saving";
  save.timer = setTimeout(() => {
    localStorage.setItem(storageKey, JSON.stringify({ ...state, savedAt: new Date().toISOString() }));
    if (autosave) autosave.textContent = "Saved just now";
    saveBackend("draft");
  }, 220);
}

async function saveBackend(status = "draft") {
  if (typeof apiRequest !== "function") return null;
  try {
    const endpoint = status === "business_complete"
      ? "/api/explore/business/complete"
      : status === "human_complete"
        ? "/api/explore/human/complete"
        : status === "planetary_complete"
          ? "/api/explore/planetary/complete"
          : "/api/explore/planetary/autosave";
    const response = await apiRequest(endpoint, {
      method: "POST",
      body: JSON.stringify({
        anonymousSessionId,
        journeyId: localStorage.getItem("greenSpectrum.activeJourneyId.v1") || "",
        formData: state
      })
    });
    if (response.outputs) localStorage.setItem(status === "business_complete" ? "greenSpectrum.businessEmpathyOutputs.v1" : "greenSpectrum.humanEmpathyOutputs.v1", JSON.stringify(response.outputs));
    if (response.intelligence) {
      state.intelligence = response.intelligence;
      localStorage.setItem("greenSpectrum.organisationIntelligence.v1", JSON.stringify(response.intelligence));
      renderIntelligencePanel(response.intelligence);
    }
    return response;
  } catch {
    return null;
  }
}

async function restoreBackend() {
  if (typeof apiRequest !== "function") return;
  try {
    const response = await apiRequest(`/api/explore/business/state?anonymousSessionId=${encodeURIComponent(anonymousSessionId)}`);
    if (response.found && response.formData?.responses) {
      state.responses = response.formData.responses;
      state.problemSignals = response.formData.problemSignals || [];
      state.intelligence = response.intelligence || JSON.parse(localStorage.getItem("greenSpectrum.organisationIntelligence.v1") || "null");
      restoreValues();
      updateExplore();
    }
  } catch {}
}

function setText(selector, value) {
  const target = document.querySelector(selector);
  if (target) target.textContent = value;
}

function titleCase(value) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function slugify(value) {
  return String(value).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (match) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#039;" }[match]));
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/"/g, "&quot;");
}

form.addEventListener("input", updateExplore);
form.addEventListener("change", updateExplore);

document.querySelectorAll("[data-empathy-select]").forEach((button) => {
  button.addEventListener("click", () => {
    const key = button.dataset.empathySelect;
    const info = document.querySelector("[data-empathy-info]");
    const total = questions.filter((item) => item.empathy === key).length;
    info.innerHTML = `<h3>${empathyMeta[key].title}</h3><p>${empathyMeta[key].copy}</p><small>${total} questions · estimated ${empathyMeta[key].time}</small><a class="button button-secondary" href="#${key}-empathy">Start or continue</a>`;
    document.querySelectorAll("[data-empathy-select]").forEach((item) => item.classList.toggle("active", item === button));
  });
});

document.addEventListener("click", (event) => {
  const nextButton = event.target.closest("[data-question-next]");
  if (nextButton) {
    updateExplore();
    const current = nextButton.closest(".question-card");
    const cards = [...document.querySelectorAll(".question-card")];
    const next = cards[cards.indexOf(current) + 1];
    if (next) next.scrollIntoView({ behavior: "smooth", block: "center" });
  }
  if (event.target.matches("[data-resource-toggle]")) {
    const panel = document.querySelector("[data-resource-panel]");
    if (panel) panel.hidden = !panel.hidden;
  }
  if (event.target.matches("[data-review-context]")) {
    alert(`Onboarding context loaded:\nOrganisation: ${onboarding.organisationName || "Missing"}\nSector: ${onboarding.industry || "Missing"}\nReason: ${Array.isArray(onboarding.reasons) ? onboarding.reasons.join(", ") : onboarding.reasons || "Missing"}`);
  }
  if (event.target.matches("[data-add-problem]")) {
    state.problemSignals.push({ title: "New problem signal", description: "Describe the issue to carry into Impact Journey Mapping.", confidence: "low", source: "User added" });
    updateExplore();
  }
  if (event.target.matches("[data-download-explore]")) {
    const blob = new Blob([JSON.stringify({ responses: state.responses, problemSignals: state.problemSignals, intelligence: state.intelligence }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `green-spectrum-explore-${event.target.dataset.downloadExplore}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }
  const toolFocus = event.target.closest("[data-tool-focus]");
  if (toolFocus) {
    const card = toolFocus.closest(".investigation-tool-card");
    if (card) {
      card.classList.add("is-highlighted");
      setTimeout(() => card.classList.remove("is-highlighted"), 1800);
    }
  }
  if (event.target.matches("[data-explore-save-exit]")) {
    updateExplore();
    window.location.href = "../";
  }
  if (event.target.matches("[data-dismiss-explore-insight]")) {
    event.target.closest(".generated-insight").hidden = true;
  }
  if (event.target.matches("[data-save-problem-signal]")) {
    const completed = completedResponses();
    const hotspot = completed.find((item) => ["white", "light", "unknown"].includes(item.maturity));
    state.problemSignals.push({ title: hotspot ? `${hotspot.area} needs deeper mapping` : "Explore insight saved", description: "Saved from the live insight panel.", confidence: hotspot?.confidence || "low", source: hotspot ? `Question ${hotspot.id}` : "Live insight" });
    updateExplore();
  }
  if (event.target.matches("[data-continue-impact]")) {
    const confirmed = document.querySelector('[name="exploreReviewConfirmed"]');
    if (!confirmed.checked) {
      event.preventDefault();
      confirmed.focus();
    }
  }
  if (event.target.matches("[data-complete-business]")) {
    updateExplore();
    saveBackend("business_complete").then(() => {
      const human = document.querySelector('[data-empathy="human"]');
      if (human) human.scrollIntoView({ behavior: "smooth", block: "center" });
      const autosave = document.querySelector("[data-explore-autosave]");
      if (autosave) autosave.textContent = "Business layer complete";
    });
  }
  if (event.target.matches("[data-complete-human]")) {
    updateExplore();
    saveBackend("human_complete").then(() => {
      const planetary = document.querySelector('[data-empathy="planetary"]');
      if (planetary) planetary.scrollIntoView({ behavior: "smooth", block: "center" });
      const autosave = document.querySelector("[data-explore-autosave]");
      if (autosave) autosave.textContent = "Human layer complete";
    });
  }
  if (event.target.matches("[data-complete-planetary]")) {
    updateExplore();
    saveBackend("planetary_complete").then(() => {
      const autosave = document.querySelector("[data-explore-autosave]");
      if (autosave) autosave.textContent = "Planetary layer complete";
      document.querySelector("#explore-synthesis")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }
});

function applyDeepLink() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("empathy") && params.get("empathy") !== "business") return;
  const questionKey = params.get("question");
  const toolKey = params.get("tool");
  const panel = params.get("panel");
  if (!questionKey) return;
  const question = businessQuestions.find((item) => String(item.id) === questionKey || slugify(item.area) === questionKey);
  if (!question) return;
  const article = document.querySelector(`[data-question="${question.id}"]`);
  if (!article) return;
  article.closest("details.theme-section")?.setAttribute("open", "");
  article.scrollIntoView({ behavior: "smooth", block: "center" });
  if (panel === "evidence") {
    [...article.querySelectorAll("details")].find((detail) => detail.querySelector("summary")?.textContent.includes("Evidence"))?.setAttribute("open", "");
  }
  if (toolKey) {
    [...article.querySelectorAll("details")].find((detail) => detail.querySelector("summary")?.textContent.includes("Recommended"))?.setAttribute("open", "");
    const tool = article.querySelector(`[data-tool="${CSS.escape(toolKey)}"]`);
    if (tool) tool.classList.add("is-highlighted");
  }
}

window.addEventListener("load", applyDeepLink);
