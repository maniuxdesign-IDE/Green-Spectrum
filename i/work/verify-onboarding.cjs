const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await page.goto("http://localhost:4173/onboarding.html", { waitUntil: "domcontentloaded" });

  const initial = await page.evaluate(() => ({
    title: document.title,
    step2Locked: document.querySelector('[data-step="2"]').classList.contains("is-locked"),
    outputHidden: document.querySelector("#journey-output").classList.contains("is-locked"),
    overflow: document.documentElement.scrollWidth > innerWidth + 1
  }));

  await page.selectOption("#industry", "Technology");
  await page.click('#question-industry [data-next-step="2"]');
  await page.check('#question-mode input[value="Hybrid"]');
  await page.click('#question-mode [data-next-step="3"]');
  await page.fill('[name="companyName"]', "Greenfield Foods");
  await page.fill('[name="companyWebsite"]', "https://greenfield.example");
  await page.selectOption('[name="companySize"]', "251-1000 people");
  await page.fill(
    '[name="companyDetails"]',
    "UK food producer with chilled logistics, packaging concerns, and retailer compliance pressure."
  );
  await page.click('#question-company [data-next-step="4"]');
  await page.fill(
    '[name="reportNotes"]',
    "Carbon baseline completed last year. Packaging and logistics data are fragmented."
  );
  await page.click('#question-reports [data-next-step="5"]');
  await page.check('input[value="Energy bills"]');
  await page.check('input[value="Logistics information"]');
  await page.check('input[value="Insurance or risk details"]');
  await page.click('#question-data [data-next-step="6"]');
  await page.check('input[value="Custom strategy"]');
  await page.check('input[value="Risk and regulation scan"]');
  await page.check('input[value="Prototype ideas"]');
  await page.click('#question-output button[type="submit"]');

  const final = await page.evaluate(() => ({
    stepLocks: [...document.querySelectorAll(".question-section")].map((section) => ({
      step: section.dataset.step,
      locked: section.classList.contains("is-locked"),
      complete: section.classList.contains("is-complete")
    })),
    outputVisible: !document.querySelector("#journey-output").classList.contains("is-locked"),
    onboardingState: document.querySelector("#onboardingState").textContent,
    profile: document.querySelector("#profileSummary").textContent.replace(/\s+/g, " ").trim(),
    outputs: [...document.querySelectorAll("#outputsSummary li")].map((li) => li.textContent.trim()),
    overflow: document.documentElement.scrollWidth > innerWidth + 1
  }));

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("http://localhost:4173/onboarding.html", { waitUntil: "domcontentloaded" });
  const mobile = await page.evaluate(() => ({
    width: innerWidth,
    overflow: document.documentElement.scrollWidth > innerWidth + 1,
    navWidth: Math.round(document.querySelector(".top-nav").getBoundingClientRect().width)
  }));

  await browser.close();
  console.log(JSON.stringify({ initial, final, mobile }, null, 2));
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
