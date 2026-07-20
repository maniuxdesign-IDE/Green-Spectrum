const fs = require("fs");
const path = require("path");

const ROOT = __dirname;

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

const simpleUtilityPages = new Set([
  "login/index.html",
  "register/index.html",
  "dashboard/index.html",
  "about/index.html",
  "help/index.html",
  "privacy/index.html",
  "terms/index.html",
  "accessibility/index.html",
]);

const checks = [];

function record(name, ok, detail = "") {
  checks.push({ name, ok, detail });
}

function plainText(html) {
  return html
    .replace(/<script[\s\S]*?<\/script>/g, "")
    .replace(/<style[\s\S]*?<\/style>/g, "")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function buttonLabels(html) {
  return [...html.matchAll(/<(?:a|button)[^>]*class="[^"]*(?:button|text-link)[^"]*"[^>]*>([\s\S]*?)<\/(?:a|button)>/g)]
    .map((match) => plainText(match[1]))
    .filter(Boolean);
}

function navLinkCount(html) {
  const nav = html.match(/<nav[^>]*class="desktop-nav"[\s\S]*?<\/nav>/);
  return nav ? (nav[0].match(/<a\b/g) || []).length : 0;
}

function auditPage(file) {
  const html = fs.readFileSync(path.join(ROOT, file), "utf8");
  const h1 = plainText(html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/)?.[1] || "");
  const labels = buttonLabels(html);
  const longLabels = labels.filter((label) => label.length > 36);

  return {
    file,
    hasMain: /<main\b/.test(html),
    hasSkipLink: /class="skip-link"/.test(html),
    h1Length: h1.length,
    navLinks: navLinkCount(html),
    longLabels,
    activeAuthLinks: [...html.matchAll(/<a\b[^>]*href="([^"]*(?:login|register|dashboard)[^"]*)"/g)].map((match) => match[1]),
  };
}

function main() {
  const results = pages.map(auditPage);

  const missingMain = results.filter((result) => !result.hasMain).map((result) => result.file);
  record("Every page has a main landmark", missingMain.length === 0, missingMain.join(", "));

  const missingSkip = results
    .filter((result) => !simpleUtilityPages.has(result.file) && !result.hasSkipLink)
    .map((result) => result.file);
  record("Core pages keep skip links", missingSkip.length === 0, missingSkip.join(", "));

  const longHeadings = results
    .filter((result) => result.h1Length > 95)
    .map((result) => `${result.file} (${result.h1Length})`);
  record("Desktop H1 lengths stay readable", longHeadings.length === 0, longHeadings.join(", "));

  const crowdedNavs = results
    .filter((result) => result.navLinks > 7)
    .map((result) => `${result.file} (${result.navLinks})`);
  record("Desktop navs are not overcrowded", crowdedNavs.length === 0, crowdedNavs.join(", "));

  const longButtons = results
    .filter((result) => result.longLabels.length)
    .map((result) => `${result.file}: ${result.longLabels.join(" | ")}`);
  record("Button labels avoid forced wrapping", longButtons.length === 0, longButtons.join("; "));

  const landing = results.find((result) => result.file === "index.html");
  record(
    "Landing stays guest-first without active auth routes",
    landing.activeAuthLinks.length === 0,
    landing.activeAuthLinks.join(", ")
  );

  const failed = checks.filter((check) => !check.ok);
  for (const check of checks) {
    console.log(`${check.ok ? "PASS" : "FAIL"} ${check.name}${check.detail ? ` :: ${check.detail}` : ""}`);
  }
  if (failed.length) process.exitCode = 1;
}

main();
