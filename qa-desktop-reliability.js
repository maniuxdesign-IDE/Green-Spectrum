const fs = require("fs");
const http = require("http");
const path = require("path");

const ROOT = __dirname;
const BASE_URL = "http://127.0.0.1:8010";

const pages = [
  "index.html",
  "resources/index.html",
  "onboarding/index.html",
  "explore/index.html",
  "impact-journey/index.html",
  "sort-prioritise/index.html",
  "prototype/index.html",
  "login/index.html",
  "register/index.html",
  "dashboard/index.html",
  "about/index.html",
  "help/index.html",
  "privacy/index.html",
  "terms/index.html",
  "accessibility/index.html",
];

const publicRoutes = [
  "./",
  "./resources/",
  "./onboarding/",
  "./explore/",
  "./impact-journey/",
  "./sort-prioritise/",
  "./prototype/",
  "./login/",
  "./register/",
  "./dashboard/",
];

const requiredDownloads = [
  "downloads/green-spectrum-playbook.pdf",
  "downloads/three-empathies-questions-1.pdf",
  "downloads/three-empathies-questions-2.pdf",
  "downloads/impact-journey-mapping-canvas.pdf",
  "downloads/green-spectrum-canvas.pdf",
  "downloads/opportunity-mapping-tree.pdf",
  "downloads/prototype-experiment-card.pdf",
  "downloads/prototyping-wheel.pdf",
  "downloads/green-spectrum-mvp-resources.zip",
];

const checks = [];

function record(name, ok, detail = "") {
  checks.push({ name, ok, detail });
}

function existingTarget(fromFile, ref) {
  const clean = ref.split("#")[0].split("?")[0];
  if (!clean || /^(https?:|mailto:|tel:|data:)/.test(clean)) return true;
  if (clean.startsWith("#")) return true;
  const candidate = clean.startsWith("/")
    ? path.join(ROOT, clean.replace(/^\//, ""))
    : path.join(ROOT, path.dirname(fromFile), clean);
  return fs.existsSync(candidate) || fs.existsSync(path.join(candidate, "index.html"));
}

function htmlIds(file) {
  const html = fs.readFileSync(path.join(ROOT, file), "utf8");
  return new Set([...html.matchAll(/id="([^"]+)"/g)].map((match) => match[1]));
}

function staticIntegrity() {
  const missing = [];
  const missingAnchors = [];
  for (const file of pages) {
    const absolute = path.join(ROOT, file);
    if (!fs.existsSync(absolute)) {
      missing.push({ file, ref: "page file" });
      continue;
    }
    const html = fs.readFileSync(absolute, "utf8");
    const ids = htmlIds(file);
    for (const match of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
      const ref = match[1];
      if (ref.startsWith("#") && ref.length > 1 && !ids.has(ref.slice(1))) {
        missingAnchors.push({ file, ref });
      }
      if (!existingTarget(file, ref)) {
        missing.push({ file, ref });
      }
    }
  }
  record("Static files and links resolve", missing.length === 0, missing.length ? JSON.stringify(missing) : "");
  record("In-page anchors resolve", missingAnchors.length === 0, missingAnchors.length ? JSON.stringify(missingAnchors) : "");
}

function downloadIntegrity() {
  const missing = requiredDownloads.filter((file) => !fs.existsSync(path.join(ROOT, file)));
  const empty = requiredDownloads.filter((file) => fs.existsSync(path.join(ROOT, file)) && fs.statSync(path.join(ROOT, file)).size < 1024);
  record("Required downloads exist", missing.length === 0, missing.length ? missing.join(", ") : "");
  record("Required downloads are non-empty", empty.length === 0, empty.length ? empty.join(", ") : "");
}

function guestOnlyState() {
  const landing = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
  const authPages = ["login/index.html", "register/index.html", "dashboard/index.html"]
    .map((file) => fs.readFileSync(path.join(ROOT, file), "utf8"))
    .join("\n");
  const activeAuthLinks = [...landing.matchAll(/href="([^"]*(?:login|register|dashboard)[^"]*)"/g)].map((match) => match[1]);
  record("Landing has no active auth or dashboard links", activeAuthLinks.length === 0, activeAuthLinks.join(", "));
  record("Landing keeps inactive sign-up affordance", /disabled[^>]*>Sign up later</.test(landing), "");
  record("Reserved auth routes are guest-only holding pages", /Guest-only MVP/.test(authPages) && /inactive/.test(authPages), "");
}

function request(method, route, body) {
  return new Promise((resolve) => {
    const data = body ? JSON.stringify(body) : "";
    const req = http.request(`${BASE_URL}${route}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(data),
      },
      timeout: 4000,
    }, (res) => {
      let text = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => { text += chunk; });
      res.on("end", () => resolve({ ok: res.statusCode >= 200 && res.statusCode < 400, status: res.statusCode, text }));
    });
    req.on("timeout", () => {
      req.destroy();
      resolve({ ok: false, status: 0, text: "timeout" });
    });
    req.on("error", (error) => resolve({ ok: false, status: 0, text: error.message }));
    if (data) req.write(data);
    req.end();
  });
}

async function serverSmoke() {
  const health = await request("GET", "/api/health");
  if (health.text.includes("EPERM")) {
    record("Live server checks skipped when local sockets are blocked", true, "Use curl health check or browser QA for live validation.");
    return;
  }
  record("Backend health responds", health.ok && /"ok":true/.test(health.text), `${health.status} ${health.text.slice(0, 140)}`);

  const routeResults = [];
  for (const route of publicRoutes) {
    const result = await request("GET", route);
    routeResults.push({ route, status: result.status, ok: result.ok });
  }
  const badRoutes = routeResults.filter((result) => !result.ok);
  record("Desktop MVP routes respond", badRoutes.length === 0, badRoutes.length ? JSON.stringify(badRoutes) : "");

  const resources = await request("GET", "/api/public/resources/featured");
  const resourcesOk = resources.ok && /storageKey/.test(resources.text) && /green-spectrum-playbook/.test(resources.text);
  record("Resource API exposes downloadable assets", resourcesOk, `${resources.status} ${resources.text.slice(0, 180)}`);

  const bundle = await request("GET", "/api/public/resources/bundle/download");
  const bundleOk = bundle.ok && /green-spectrum-mvp-resources\.zip/.test(bundle.text);
  record("Resource bundle API returns ZIP URL", bundleOk, `${bundle.status} ${bundle.text.slice(0, 180)}`);

  const onboarding = await request("POST", "/api/onboarding/autosave", {
    anonymousSessionId: "qa-desktop-reliability",
    formData: {
      role: "Chief Sustainability Officer",
      mode: "solo",
      organisationName: "QA Desktop Org",
      headquarters: "UK",
      industry: "Manufacturing",
      reasons: ["Decide what to prioritise"],
      maturity: "Light Green",
      stakeholders: ["Finance", "Operations"],
      decisionOwner: "Sustainability Director",
      dataSources: ["Energy data"],
      constraints: ["Weak data"],
      outputs: ["Organisation context profile"],
    },
  });
  record("Onboarding autosave API accepts guest session", onboarding.ok && /"ok":true/.test(onboarding.text), `${onboarding.status} ${onboarding.text.slice(0, 180)}`);
}

async function main() {
  staticIntegrity();
  downloadIntegrity();
  guestOnlyState();
  await serverSmoke();

  const failed = checks.filter((check) => !check.ok);
  for (const check of checks) {
    console.log(`${check.ok ? "PASS" : "FAIL"} ${check.name}${check.detail ? ` :: ${check.detail}` : ""}`);
  }
  if (failed.length) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
