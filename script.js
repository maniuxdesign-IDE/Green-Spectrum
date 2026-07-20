const header = document.querySelector("[data-header]");
const scrollHero = document.querySelector("[data-scroll-hero]");
const menuToggle = document.querySelector("[data-menu-toggle]");
const mobileMenu = document.querySelector("[data-mobile-menu]");
const modalOpeners = document.querySelectorAll("[data-modal-open]");
const modalClosers = document.querySelectorAll("[data-modal-close]");
const reveals = document.querySelectorAll(".reveal");
const apiBase = window.location.protocol === "file:" ? "" : window.location.origin;
const sessionStorageKey = "greenSpectrum.sessionId.v1";
const consentStorageKey = "greenSpectrum.consent.v1";
const testModeStorageKey = "greenSpectrum.testMode.v1";
const anonymousSessionId = localStorage.getItem(sessionStorageKey) || (crypto.randomUUID ? crypto.randomUUID() : `anon-${Date.now()}-${Math.random().toString(16).slice(2)}`);
localStorage.setItem(sessionStorageKey, anonymousSessionId);

const testModePages = [
  {
    title: "Welcome",
    href: "/",
    sections: [
      ["Hero", "/#hero"],
      ["Why Green Spectrum", "/#why-green-spectrum"],
      ["Six-step process", "/#six-step-process"],
      ["Outputs", "/#outputs"]
    ]
  },
  {
    title: "Start Your Journey",
    href: "/onboarding/",
    sections: [
      ["Intro", "/onboarding/#onboarding-intro"],
      ["Sections", "/onboarding/#onboarding-sections"],
      ["Profile", "/onboarding/#profile"],
      ["Help", "/onboarding/#onboarding-faq"]
    ]
  },
  {
    title: "Explore",
    href: "/explore/",
    sections: [
      ["Intro", "/explore/#explore-intro"],
      ["Three Empathies", "/explore/#three-empathies"],
      ["Business", "/explore/#business-empathy"],
      ["Human", "/explore/#human-empathy"],
      ["Planetary", "/explore/#planetary-empathy"]
    ]
  },
  {
    title: "Impact Journey",
    href: "/impact-journey/",
    sections: [
      ["Intro", "/impact-journey/#impact-journey-intro"],
      ["Scope", "/impact-journey/#journey-scope"],
      ["Map board", "/impact-journey/#journey-board"],
      ["Relationships", "/impact-journey/#relationships"],
      ["Review", "/impact-journey/#impact-review"]
    ]
  },
  {
    title: "Sort and Prioritise",
    href: "/sort-prioritise/",
    sections: [
      ["Intro", "/sort-prioritise/#prioritise-intro"],
      ["Portfolio", "/sort-prioritise/#problem-portfolio"],
      ["Classify", "/sort-prioritise/#classify-problems"],
      ["Score", "/sort-prioritise/#score-problems"],
      ["Recommendations", "/sort-prioritise/#recommendations"]
    ]
  },
  {
    title: "Prototype",
    href: "/prototype/",
    sections: [
      ["Intro", "/prototype/#prototype-intro"],
      ["Selected pathways", "/prototype/#selected-pathways"],
      ["Prototype builder", "/prototype/#prototype-builder"],
      ["Summary", "/prototype/#prototype-summary"],
      ["Help", "/prototype/#prototype-faq"]
    ]
  },
  {
    title: "Resources",
    href: "/resources/",
    sections: [
      ["Downloads", "/resources/#downloads"],
      ["Canvases", "/resources/#canvases"],
      ["Playbook", "/resources/#playbook"]
    ]
  }
];

const testModeEnabled = () => localStorage.getItem(testModeStorageKey) === "on";

const setTestMode = (enabled) => {
  localStorage.setItem(testModeStorageKey, enabled ? "on" : "off");
  document.documentElement.classList.toggle("test-mode-enabled", enabled);
  document.querySelector("[data-test-mode-toggle]")?.setAttribute("aria-pressed", String(enabled));
  const status = document.querySelector("[data-test-mode-status]");
  if (status) status.textContent = enabled ? "On: free navigation enabled" : "Off: guided sequence";
};

const normaliseCurrentPath = () => {
  const path = window.location.pathname;
  if (path === "/" || path === "") return "/";
  return path.endsWith("/") ? path : `${path}/`;
};

const createTestModeLauncher = () => {
  if (document.querySelector("[data-test-mode-shell]")) return;
  const currentPath = normaliseCurrentPath();
  const shell = document.createElement("aside");
  shell.className = "test-mode-shell";
  shell.dataset.testModeShell = "";
  shell.innerHTML = `
    <button class="test-mode-button" type="button" aria-expanded="false" aria-controls="test-mode-panel" data-test-mode-button>
      <span>Test mode</span>
    </button>
    <div class="test-mode-panel" id="test-mode-panel" hidden data-test-mode-panel>
      <div class="test-mode-panel-header">
        <div>
          <strong>Prototype test mode</strong>
          <p data-test-mode-status>${testModeEnabled() ? "On: free navigation enabled" : "Off: guided sequence"}</p>
        </div>
        <button type="button" aria-label="Close test mode panel" data-test-mode-close>x</button>
      </div>
      <div class="test-mode-control">
        <button class="button button-primary" type="button" aria-pressed="${testModeEnabled()}" data-test-mode-toggle>${testModeEnabled() ? "Turn off test mode" : "Turn on test mode"}</button>
        <p>Use this during moderated testing to jump between pages and sections without following the normal sequence.</p>
      </div>
      <nav class="test-mode-jump-list" aria-label="Test mode jump navigation">
        ${testModePages.map((page) => `
          <section class="${currentPath === page.href ? "is-current" : ""}">
            <a class="test-mode-page-link" href="${page.href}">${page.title}</a>
            <div>
              ${page.sections.map(([label, href]) => `<a href="${href}">${label}</a>`).join("")}
            </div>
          </section>
        `).join("")}
      </nav>
      <div class="test-mode-footer">
        <button type="button" data-test-mode-seed>Load lightweight demo data</button>
        <button type="button" data-test-mode-clear>Clear local test data</button>
      </div>
    </div>
  `;
  document.body.appendChild(shell);
  setTestMode(testModeEnabled());
};

const seedTestModeData = () => {
  const demoOrg = {
    role: "Prototype tester",
    mode: "solo",
    organisationName: "Test Mode Demo Organisation",
    headquarters: "UK",
    industry: "Manufacturing and services",
    reasons: ["Test the Green Spectrum journey"],
    maturity: "Light Green",
    stakeholders: ["Leadership", "Operations", "Employees", "Customers", "Suppliers"],
    decisionOwner: "Test facilitator",
    dataSources: ["Workshop knowledge", "Sample operational data"],
    constraints: ["Incomplete evidence", "Limited testing time"],
    outputs: ["Priority portfolio", "Prototype experiment card"]
  };
  const demoExplore = {
    responses: {
      "1": { id: 1, empathy: "business", area: "Strategy and Purpose", maturity: "light", confidence: "medium", evidence: "test mode sample", notes: "Sustainability is recognised but not yet consistently linked to decisions." },
      "17": { id: 17, empathy: "human", area: "Stakeholder Power", maturity: "light", confidence: "medium", evidence: "test mode sample", notes: "Employees and suppliers are affected but have limited influence over priorities." },
      "30": { id: 30, empathy: "planetary", area: "Environmental Impact", maturity: "light", confidence: "low", evidence: "test mode sample", notes: "Energy, materials and supplier impacts need clearer evidence." }
    }
  };
  const stageA = "test-stage-1";
  const stageB = "test-stage-2";
  const stageC = "test-stage-3";
  const demoImpact = {
    stateId: "",
    scope: { journeyType: "product-value-chain", primaryFocus: "Demo test journey", timeframe: "Current state", startPoint: "Procurement", endPoint: "Customer use", mapReviewed: "yes" },
    stages: [
      { id: stageA, name: "Procurement", description: "Supplier decisions and evidence quality", confidence: "medium", source: "test-mode" },
      { id: stageB, name: "Operations", description: "Energy, materials and staff routines", confidence: "medium", source: "test-mode" },
      { id: stageC, name: "Customer use", description: "Product or service impact in use", confidence: "low", source: "test-mode" }
    ],
    layerItems: {
      [stageA]: { activities: [{ id: "a1", title: "Supplier selection", confidence: "medium" }], business: [{ id: "b1", title: "Cost-led procurement", confidence: "medium" }], unknowns: [{ id: "u1", title: "Supplier impact data is incomplete", confidence: "low" }] },
      [stageB]: { activities: [{ id: "a2", title: "Operational delivery", confidence: "medium" }], environmental: [{ id: "e1", title: "Energy and material impact", confidence: "medium" }], social: [{ id: "s1", title: "Staff workload and capability", confidence: "medium" }] },
      [stageC]: { activities: [{ id: "a3", title: "Customer use", confidence: "low" }], environmental: [{ id: "e2", title: "Use-phase emissions uncertainty", confidence: "low" }] }
    },
    relationships: [
      { id: "r1", source: stageA, target: stageB, type: "Dependency", confidence: "Medium", description: "Supplier evidence affects operational choices." },
      { id: "r2", source: stageB, target: stageC, type: "Feedback loop", confidence: "Low", description: "Customer use learning should feed back into operations." }
    ],
    problemSignals: [{ id: "p1", title: "Supplier evidence gap", stageId: stageA, description: "Supplier data is not strong enough to support confident prioritisation.", confidence: "low", control: "medium" }],
    opportunities: [{ id: "o1", title: "Run an evidence sprint", description: "Test whether a small supplier evidence request improves decisions." }]
  };
  localStorage.setItem("greenSpectrum.onboarding.v1", JSON.stringify(demoOrg));
  localStorage.setItem("greenSpectrum.explore.v1", JSON.stringify(demoExplore));
  localStorage.setItem("greenSpectrum.impactJourney.v1", JSON.stringify(demoImpact));
  localStorage.removeItem("greenSpectrum.priority.v1");
  localStorage.removeItem("greenSpectrum.prototype.v1");
  analytics("test_mode_demo_data_loaded");
  window.location.reload();
};

const clearTestModeData = () => {
  ["greenSpectrum.onboarding.v1", "greenSpectrum.explore.v1", "greenSpectrum.impactJourney.v1", "greenSpectrum.priority.v1", "greenSpectrum.prototype.v1"].forEach((key) => localStorage.removeItem(key));
  analytics("test_mode_local_data_cleared");
  window.location.reload();
};

createTestModeLauncher();

document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-test-mode-button]");
  if (button) {
    const panel = document.querySelector("[data-test-mode-panel]");
    const isOpen = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", String(!isOpen));
    if (panel) panel.hidden = isOpen;
    return;
  }

  if (event.target.closest("[data-test-mode-close]")) {
    const launcher = document.querySelector("[data-test-mode-button]");
    const panel = document.querySelector("[data-test-mode-panel]");
    launcher?.setAttribute("aria-expanded", "false");
    if (panel) panel.hidden = true;
    return;
  }

  if (event.target.closest("[data-test-mode-toggle]")) {
    const enabled = !testModeEnabled();
    setTestMode(enabled);
    event.target.closest("[data-test-mode-toggle]").textContent = enabled ? "Turn off test mode" : "Turn on test mode";
    return;
  }

  if (event.target.closest("[data-test-mode-seed]")) {
    seedTestModeData();
    return;
  }

  if (event.target.closest("[data-test-mode-clear]")) {
    clearTestModeData();
  }
});

const getConsent = () => {
  try {
    return JSON.parse(localStorage.getItem(consentStorageKey) || '{"essential":true,"analytics":false,"decided":false}');
  } catch {
    return { essential: true, analytics: false, decided: false };
  }
};

const apiRequest = async (path, options = {}) => {
  if (!apiBase) throw new Error("API unavailable when opened from the filesystem");
  const response = await fetch(`${apiBase}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  if (!response.ok) throw new Error(`API request failed: ${response.status}`);
  return response.json();
};

const analytics = (eventName, detail = {}) => {
  const consent = getConsent();
  window.greenSpectrumEvents = window.greenSpectrumEvents || [];
  const event = { eventName, detail, at: new Date().toISOString() };
  window.greenSpectrumEvents.push(event);
  if (!consent.analytics) return;
  apiRequest("/api/analytics/events", {
    method: "POST",
    body: JSON.stringify({
      eventName,
      route: window.location.pathname,
      sectionKey: detail.sectionKey || detail.section || "",
      metadata: detail,
      anonymousSessionId,
      consentState: consent
    })
  }).catch(() => {});
};

if (document.querySelector("#hero")) {
  analytics("landing_page_view");
}

let targetHeroProgress = 0;
let currentHeroProgress = 0;
let heroFrame = null;

const calculateHeroTarget = () => {
  if (scrollHero) {
    const heroHeight = scrollHero.offsetHeight || window.innerHeight;
    const rawProgress = Math.min(1, Math.max(0, window.scrollY / Math.max(1, heroHeight - window.innerHeight)));
    return rawProgress * rawProgress * (3 - (2 * rawProgress));
  }
  return 0;
};

const delayedSmoothProgress = (progress, start, end) => {
  const normalised = Math.min(1, Math.max(0, (progress - start) / Math.max(0.001, end - start)));
  return normalised * normalised * (3 - (2 * normalised));
};

const renderHeroState = () => {
  targetHeroProgress = calculateHeroTarget();
  currentHeroProgress += (targetHeroProgress - currentHeroProgress) * 0.14;
  if (Math.abs(targetHeroProgress - currentHeroProgress) < 0.001) {
    currentHeroProgress = targetHeroProgress;
  }
  if (scrollHero) {
    scrollHero.style.setProperty("--hero-progress", currentHeroProgress.toFixed(3));
    scrollHero.style.setProperty("--hero-copy-rise", delayedSmoothProgress(currentHeroProgress, 0.72, 1).toFixed(3));
  }
  header?.classList.toggle("is-scrolled", scrollHero ? currentHeroProgress > 0.56 : window.scrollY > 18);
  if (Math.abs(targetHeroProgress - currentHeroProgress) >= 0.001) {
    heroFrame = requestAnimationFrame(renderHeroState);
  } else {
    heroFrame = null;
  }
};

const requestHeaderState = () => {
  targetHeroProgress = calculateHeroTarget();
  if (heroFrame) return;
  heroFrame = requestAnimationFrame(renderHeroState);
};

currentHeroProgress = calculateHeroTarget();
if (scrollHero) {
  scrollHero.style.setProperty("--hero-progress", currentHeroProgress.toFixed(3));
  scrollHero.style.setProperty("--hero-copy-rise", delayedSmoothProgress(currentHeroProgress, 0.72, 1).toFixed(3));
}
header?.classList.toggle("is-scrolled", scrollHero ? currentHeroProgress > 0.56 : window.scrollY > 18);
window.addEventListener("scroll", requestHeaderState, { passive: true });
window.addEventListener("resize", requestHeaderState, { passive: true });

menuToggle?.addEventListener("click", () => {
  const isOpen = menuToggle.getAttribute("aria-expanded") === "true";
  menuToggle.setAttribute("aria-expanded", String(!isOpen));
  mobileMenu.hidden = isOpen;
  document.body.classList.toggle("menu-open", !isOpen);
});

mobileMenu?.addEventListener("click", (event) => {
  if (event.target.matches("a")) {
    menuToggle?.setAttribute("aria-expanded", "false");
    mobileMenu.hidden = true;
    document.body.classList.remove("menu-open");
  }
});

if ("IntersectionObserver" in window) {
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.14, rootMargin: "0px 0px -8% 0px" });

  reveals.forEach((item) => revealObserver.observe(item));
} else {
  reveals.forEach((item) => item.classList.add("is-visible"));
}

const stageCards = document.querySelectorAll(".stage-card");
if ("IntersectionObserver" in window) {
  const stageObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const index = [...stageCards].indexOf(entry.target) + 1;
        analytics("landing_process_stage_viewed", { stage: index });
      }
    });
  }, { threshold: 0.55 });
  stageCards.forEach((card) => stageObserver.observe(card));
}

document.querySelectorAll("details").forEach((detail) => {
  detail.addEventListener("toggle", () => {
    if (!detail.open) return;
    const label = detail.querySelector("summary")?.textContent?.trim();
    const isStage = detail.closest(".stage-card");
    analytics(isStage ? "landing_process_stage_expanded" : "landing_faq_opened", { label });
  });
});

document.querySelectorAll("[data-analytics]").forEach((item) => {
  item.addEventListener("click", () => analytics(item.dataset.analytics));
});

document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", (event) => {
    const target = document.querySelector(anchor.getAttribute("href"));
    if (!target) return;
    event.preventDefault();
    const top = target.getBoundingClientRect().top + window.scrollY - 72;
    window.scrollTo({ top, behavior: "smooth" });
    history.pushState(null, "", anchor.getAttribute("href"));
  });
});

modalOpeners.forEach((opener) => {
  opener.addEventListener("click", () => {
    const modal = document.querySelector(`[data-modal="${opener.dataset.modalOpen}"]`);
    if (!modal) return;
    modal.hidden = false;
    modal.querySelector(".modal-close")?.focus();
    analytics("landing_usage_mode_selected", { mode: opener.dataset.modalOpen });
  });
});

const closeModal = (modal) => {
  modal.hidden = true;
};

modalClosers.forEach((closer) => {
  closer.addEventListener("click", () => closeModal(closer.closest(".modal")));
});

document.querySelectorAll(".modal").forEach((modal) => {
  modal.addEventListener("click", (event) => {
    if (event.target === modal) closeModal(modal);
  });
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    document.querySelectorAll(".modal:not([hidden])").forEach(closeModal);
    if (!mobileMenu?.hidden) {
      menuToggle?.setAttribute("aria-expanded", "false");
      mobileMenu.hidden = true;
      document.body.classList.remove("menu-open");
    }
  }
});

const scrollMarks = new Set();
window.addEventListener("scroll", () => {
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  if (scrollable <= 0) return;
  const progress = Math.round((window.scrollY / scrollable) * 100);
  [25, 50, 75, 100].forEach((mark) => {
    if (progress >= mark && !scrollMarks.has(mark)) {
      scrollMarks.add(mark);
      analytics(`landing_scroll_${mark}`);
    }
  });
}, { passive: true });

const onboardingForm = document.querySelector("[data-onboarding-form]");
if (onboardingForm) {
  const storageKey = "greenSpectrum.onboarding.v1";
  const sections = [...document.querySelectorAll(".onboarding-section")];
  const progressLabel = document.querySelector("[data-progress-label]");
  const timeRemaining = document.querySelector("[data-time-remaining]");
  const progressFill = document.querySelector("[data-progress-fill]");
  const autosave = document.querySelector("[data-autosave]");
  const summaryList = document.querySelector("[data-summary-list]");
  const roleInsight = document.querySelector("[data-role-insight]");
  const websiteNote = document.querySelector("[data-website-note]");
  const fileInput = onboardingForm.querySelector('input[type="file"]');
  const fileList = document.querySelector("[data-file-list]");
  const insight = document.querySelector("[data-generated-insight] p");
  const backendStatus = document.querySelector("[data-backend-status] p");
  const routeStart = document.querySelector("[data-route-start]");
  const routeRationale = document.querySelector("[data-route-rationale]");
  const routeThemes = document.querySelector("[data-route-themes]");
  const requiredSections = ["role", "mode", "organisation", "sector", "reason", "maturity", "stakeholders", "constraints", "outputs"];

  analytics("onboarding_started");

  const getValues = () => {
    const data = {};
    const formData = new FormData(onboardingForm);
    for (const [key, value] of formData.entries()) {
      if (value instanceof File) continue;
      if (data[key]) {
        data[key] = Array.isArray(data[key]) ? [...data[key], value] : [data[key], value];
      } else {
        data[key] = value;
      }
    }
    data.fileNames = fileInput ? [...fileInput.files].map((file) => file.name) : [];
    return data;
  };

  const setValues = (data) => {
    Object.entries(data || {}).forEach(([key, value]) => {
      if (key === "fileNames") return;
      const values = Array.isArray(value) ? value : [value];
      values.forEach((item) => {
        const field = onboardingForm.querySelector(`[name="${CSS.escape(key)}"][value="${CSS.escape(item)}"]`);
        if (field && (field.type === "checkbox" || field.type === "radio")) field.checked = true;
      });
      const field = onboardingForm.querySelector(`[name="${CSS.escape(key)}"]:not([type="checkbox"]):not([type="radio"])`);
      if (field) field.value = value;
    });
    if (data?.fileNames?.length && fileList) fileList.textContent = data.fileNames.join(", ");
  };

  const valueText = (value, fallback = "Missing") => {
    if (Array.isArray(value)) return value.filter(Boolean).join(", ") || fallback;
    return value || fallback;
  };

  const sectionComplete = (section) => {
    const key = section.dataset.section;
    const values = getValues();
    if (key === "role") return Boolean(values.role);
    if (key === "mode") return Boolean(values.mode);
    if (key === "organisation") return Boolean(values.organisationName && values.headquarters);
    if (key === "sector") return Boolean(values.industry);
    if (key === "reason") return Boolean(values.reasons);
    if (key === "maturity") return Boolean(values.maturity);
    if (key === "stakeholders") return Boolean(values.stakeholders || values.decisionOwner);
    if (key === "constraints") return Boolean(values.priorityDrivers || values.constraints || values.timeHorizon);
    if (key === "outputs") return Boolean(values.outputs);
    return Boolean(values.evidence || values.dataSources);
  };

  const renderRecommendedRoute = (route) => {
    if (!route) return;
    if (routeStart) routeStart.textContent = `Start with ${route.startWith || "Business Empathy"}`;
    if (routeRationale) {
      const rationale = Array.isArray(route.rationale) ? route.rationale.join(" ") : route.rationale;
      routeRationale.textContent = rationale || "Green Spectrum will keep the default Explore order until more context is available.";
    }
    if (routeThemes) {
      routeThemes.innerHTML = (route.priorityThemes || []).map((theme) => `<li>${theme}</li>`).join("");
    }
  };

  const saveBackend = async (values, status = "draft") => {
    if (backendStatus) backendStatus.textContent = "Syncing with backend";
    try {
      const response = await apiRequest(status === "completed" ? "/api/onboarding/complete" : "/api/onboarding/autosave", {
        method: "POST",
        body: JSON.stringify({ anonymousSessionId, formData: values })
      });
      if (response.contextProfile) {
        localStorage.setItem("greenSpectrum.contextProfile.v1", JSON.stringify(response.contextProfile));
      }
      if (response.recommendedRoute) {
        localStorage.setItem("greenSpectrum.recommendedRoute.v1", JSON.stringify(response.recommendedRoute));
        renderRecommendedRoute(response.recommendedRoute);
      }
      if (response.journeyId) localStorage.setItem("greenSpectrum.activeJourneyId.v1", response.journeyId);
      if (response.organisationId) localStorage.setItem("greenSpectrum.activeOrganisationId.v1", response.organisationId);
      if (backendStatus) backendStatus.textContent = status === "completed" ? "Journey and organisation records created" : "Synced to backend";
      return response;
    } catch {
      if (backendStatus) backendStatus.textContent = "Offline fallback active. Your work is saved in this browser.";
      return null;
    }
  };

  const updateSummary = () => {
    const values = getValues();
    const rows = [
      ["Organisation", valueText(values.organisationName), values.organisationName ? "Confirmed" : "Missing"],
      ["Role", valueText(values.role), values.role ? "Confirmed" : "Missing"],
      ["Journey mode", valueText(values.mode), values.mode ? "Confirmed" : "Missing"],
      ["Sector", valueText(values.industry), values.industry ? "Confirmed" : "Missing"],
      ["Reason for starting", valueText(values.reasons), values.reasons ? "User estimate" : "Missing"],
      ["Stakeholders", valueText(values.stakeholders || values.participants), values.stakeholders || values.participants ? "User estimate" : "Missing"],
      ["Decision owner", valueText(values.decisionOwner), values.decisionOwner ? "User estimate" : "Missing"],
      ["Provisional maturity", valueText(values.maturity), values.maturity ? "User estimate" : "Missing"],
      ["Evidence available", valueText(values.evidence || values.fileNames), values.evidence || values.fileNames?.length ? "User estimate" : "Missing"],
      ["Data available", valueText(values.dataSources), values.dataSources ? "User estimate" : "Missing"],
      ["Key constraints", valueText(values.constraints), values.constraints ? "User estimate" : "Missing"],
      ["Desired outputs", valueText(values.outputs), values.outputs ? "Confirmed" : "Missing"]
    ];
    if (summaryList) {
      summaryList.innerHTML = rows.map(([label, value, confidence]) => `
        <div class="summary-row">
          <dt>${label}</dt>
          <dd>${value} <span class="confidence-badge">${confidence}</span></dd>
        </div>
      `).join("");
    }

    if (roleInsight) {
      const role = values.role || "";
      const text = role.includes("Reporting")
        ? "Guidance will emphasise evidence quality, confidence labels and export-ready summaries."
        : role.includes("Facilitator") || role.includes("Consultant")
          ? "Guidance will emphasise stakeholder alignment, facilitation moments and structured outputs."
          : role.includes("Operations") || role.includes("Finance")
            ? "Guidance will emphasise practical constraints, ownership, data access and decision criteria."
            : values.role
              ? "Guidance will emphasise strategic decisions, stakeholder alignment and executive-ready outputs."
              : "Guidance will adapt to your role once selected.";
      roleInsight.textContent = text;
    }

    if (websiteNote) websiteNote.hidden = !values.website;
    if (insight) {
      const clarity = values.challengeClarity || "";
      const mode = values.mode || "solo";
      const constraint = valueText(values.constraints, "current constraints");
      const stakeholderSignal = values.stakeholders ? ` Key stakeholders include ${valueText(values.stakeholders)}.` : "";
      insight.textContent = clarity.includes("symptoms") || clarity.includes("broadly")
        ? `Your ${mode} journey is likely to benefit from a broad Explore stage focused on ${constraint}.${stakeholderSignal}`
        : `Your ${mode} journey can begin with a focused Explore stage while keeping evidence confidence visible.${stakeholderSignal}`;
    }
  };

  const updateProgress = () => {
    const completed = sections.filter(sectionComplete).length;
    const percent = Math.round((completed / sections.length) * 100);
    sections.forEach((section) => {
      const state = section.querySelector("[data-state]");
      if (!state) return;
      const optional = ["evidence", "data"].includes(section.dataset.section);
      state.textContent = sectionComplete(section) ? "Complete" : optional ? "Optional" : section.open ? "In progress" : "Not started";
    });
    if (progressLabel) progressLabel.textContent = `${completed} of ${sections.length} sections complete`;
    if (timeRemaining) timeRemaining.textContent = `Approximately ${Math.max(1, 10 - completed)} minutes remaining`;
    if (progressFill) progressFill.style.width = `${percent}%`;
    updateSummary();
  };

  const save = () => {
    autosave && (autosave.textContent = "Saving");
    window.clearTimeout(save.timer);
    save.timer = window.setTimeout(() => {
      localStorage.setItem(storageKey, JSON.stringify({ ...getValues(), savedAt: new Date().toISOString() }));
      autosave && (autosave.textContent = "Saved just now");
      saveBackend(getValues());
      analytics("onboarding_saved");
    }, 240);
  };

  setValues(JSON.parse(localStorage.getItem(storageKey) || "{}"));
  const restoreBackend = async () => {
    try {
      const state = await apiRequest(`/api/onboarding/state?anonymousSessionId=${encodeURIComponent(anonymousSessionId)}`);
      if (state.found && state.formData) {
        setValues(state.formData);
        localStorage.setItem(storageKey, JSON.stringify({ ...state.formData, savedAt: state.updatedAt }));
        renderRecommendedRoute(state.recommendedRoute);
        if (backendStatus) backendStatus.textContent = "Restored from backend";
      } else if (backendStatus) {
        backendStatus.textContent = "Ready to sync with backend";
      }
      updateProgress();
    } catch {
      if (backendStatus) backendStatus.textContent = "Offline fallback active. Your work is saved in this browser.";
    }
  };
  restoreBackend();
  renderRecommendedRoute(JSON.parse(localStorage.getItem("greenSpectrum.recommendedRoute.v1") || "null"));
  updateProgress();

  onboardingForm.addEventListener("input", () => {
    updateProgress();
    save();
  });
  onboardingForm.addEventListener("change", () => {
    updateProgress();
    save();
  });

  sections.forEach((section) => {
    section.addEventListener("toggle", () => {
      if (section.open) analytics("onboarding_section_opened", { section: section.dataset.section });
    });
  });

  document.querySelectorAll("[data-next]").forEach((button) => {
    button.addEventListener("click", () => {
      const current = button.closest(".onboarding-section");
      if (!current) return;
      const required = requiredSections.includes(current.dataset.section);
      if (required && !sectionComplete(current)) {
        const firstInput = current.querySelector("input, select, textarea");
        firstInput?.focus();
        autosave && (autosave.textContent = "Add the required information to continue");
        return;
      }
      const next = sections[sections.indexOf(current) + 1];
      current.open = false;
      if (next) {
        next.open = true;
        next.scrollIntoView({ behavior: "smooth", block: "center" });
      } else {
        document.querySelector("#review-and-confirm")?.scrollIntoView({ behavior: "smooth", block: "start" });
      }
      updateProgress();
      save();
    });
  });

  fileInput?.addEventListener("change", () => {
    const names = [...fileInput.files].map((file) => file.name);
    fileList.textContent = names.length ? names.join(", ") : "No files selected";
    analytics("onboarding_evidence_uploaded", { count: names.length });
  });

  document.querySelector("[data-help-toggle]")?.addEventListener("click", () => {
    const panel = document.querySelector("[data-help-panel]");
    if (panel) panel.hidden = !panel.hidden;
    analytics("onboarding_help_opened");
  });

  document.querySelector("[data-dismiss-insight]")?.addEventListener("click", (event) => {
    event.currentTarget.closest(".generated-insight").hidden = true;
  });

  document.querySelector("[data-download-summary]")?.addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(getValues(), null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "green-spectrum-onboarding-summary.json";
    link.click();
    URL.revokeObjectURL(url);
  });

  document.querySelectorAll("[data-save-exit]").forEach((button) => {
    button.addEventListener("click", () => {
      save();
      window.location.href = "../";
    });
  });

  document.querySelector("[data-complete-onboarding]")?.addEventListener("click", (event) => {
    const values = getValues();
    if (!values.confirmAccuracy || !values.confirmVerification) {
      event.preventDefault();
      document.querySelector('input[name="confirmAccuracy"]')?.focus();
      autosave && (autosave.textContent = "Confirm the two required statements before continuing");
      return;
    }
    event.preventDefault();
    autosave && (autosave.textContent = "Creating journey records");
    saveBackend(values, "completed").then((response) => {
      analytics("onboarding_completed");
      window.location.href = response?.nextRoute || "../explore/";
    });
  });
}

const applyJourneyEntryState = async () => {
  const ctas = document.querySelectorAll("[data-journey-cta]");
  if (!ctas.length) return;
  try {
    const state = await apiRequest("/api/session/journey-entry");
    ctas.forEach((cta) => {
      cta.textContent = state.ctaLabel || "Start Your Journey";
      cta.setAttribute("href", state.ctaRoute || "/onboarding/");
      cta.dataset.authenticated = String(Boolean(state.authenticated));
      cta.dataset.activeJourney = String(Boolean(state.activeJourney));
    });
  } catch {
    ctas.forEach((cta) => {
      cta.textContent = "Start Your Journey";
      cta.setAttribute("href", cta.getAttribute("href") || "/onboarding/");
    });
  }
};

const loadLandingBackendContent = async () => {
  const versionTarget = document.querySelector("[data-methodology-version]");
  if (!versionTarget) return;
  try {
    const data = await apiRequest("/api/public/landing");
    if (data.methodologyVersion?.version) {
      versionTarget.textContent = `Methodology version ${data.methodologyVersion.version}`;
      versionTarget.hidden = false;
    }
  } catch {
    versionTarget.hidden = true;
  }
};

const setupResourceBundleAction = () => {
  document.querySelectorAll("[data-download-bundle]").forEach((button) => {
    button.addEventListener("click", async () => {
      analytics("landing_download_bundle_clicked", { ctaLocation: "resources" });
      button.setAttribute("aria-busy", "true");
      try {
        const bundle = await apiRequest("/api/public/resources/bundle/download");
        if (bundle.available && bundle.downloadUrl) {
          window.location.href = bundle.downloadUrl;
        } else {
          const message = document.querySelector("[data-resource-status]");
          if (message) message.textContent = bundle.message || "Downloads are temporarily unavailable. Please browse the Resources library.";
          window.setTimeout(() => { window.location.href = "resources/"; }, 700);
        }
      } catch {
        window.location.href = "resources/";
      } finally {
        button.removeAttribute("aria-busy");
      }
    });
  });
};

const setupConsentBanner = () => {
  const consent = getConsent();
  if (consent.decided || !document.body) return;
  const banner = document.createElement("section");
  banner.className = "consent-banner";
  banner.setAttribute("aria-label", "Privacy and analytics choices");
  banner.innerHTML = `
    <div>
      <h2>Privacy choices</h2>
      <p>Green Spectrum uses essential storage for this local prototype. Optional analytics help understand which public sections are useful. No organisational information is collected on this page.</p>
    </div>
    <div class="consent-actions">
      <button class="button button-secondary" type="button" data-consent-decline>Essential only</button>
      <button class="button button-primary" type="button" data-consent-accept>Allow analytics</button>
    </div>
  `;
  document.body.appendChild(banner);

  const saveConsent = (analyticsGranted) => {
    const nextConsent = { essential: true, analytics: analyticsGranted, decided: true, version: "2026-07-landing-v1" };
    localStorage.setItem(consentStorageKey, JSON.stringify(nextConsent));
    apiRequest("/api/consent", {
      method: "POST",
      body: JSON.stringify({ anonymousSessionId, consent: nextConsent })
    }).catch(() => {});
    banner.remove();
    if (analyticsGranted) {
      window.greenSpectrumEvents?.forEach((event) => analytics(event.eventName, event.detail));
    }
  };

  banner.querySelector("[data-consent-decline]")?.addEventListener("click", () => saveConsent(false));
  banner.querySelector("[data-consent-accept]")?.addEventListener("click", () => saveConsent(true));
};

applyJourneyEntryState();
loadLandingBackendContent();
setupResourceBundleAction();
setupConsentBanner();
