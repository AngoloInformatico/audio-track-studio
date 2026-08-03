import process from "node:process";
import { chromium } from "playwright-core";

const [screenshotPath] = process.argv.slice(2);
const edgePath = process.env.ATS_EDGE_PATH
  ?? "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const appUrl = process.env.ATS_E2E_URL ?? "http://127.0.0.1:5173";
const browser = await chromium.launch({ executablePath: edgePath, headless: true });

try {
  const page = await browser.newPage({ viewport: { width: 1180, height: 700 } });
  await page.goto(appUrl, { waitUntil: "networkidle" });
  const link = page.locator(".main-copyright");
  await link.waitFor();
  const metrics = await page.evaluate(() => {
    const footer = document.querySelector(".main-copyright-footer");
    const anchor = document.querySelector(".main-copyright");
    if (!(footer instanceof HTMLElement) || !(anchor instanceof HTMLAnchorElement)) return null;
    const rect = footer.getBoundingClientRect();
    return {
      footerBottom: Math.round(rect.bottom),
      footerTop: Math.round(rect.top),
      href: anchor.href,
      innerHeight: window.innerHeight,
      scrollHeight: document.documentElement.scrollHeight,
      text: anchor.textContent?.trim(),
    };
  });
  if (!metrics) throw new Error("Footer copyright non trovato.");
  if (metrics.scrollHeight > metrics.innerHeight) {
    throw new Error(`La pagina vuota scorre: ${metrics.scrollHeight}px > ${metrics.innerHeight}px.`);
  }
  if (metrics.footerBottom !== metrics.innerHeight || metrics.footerTop < 0) {
    throw new Error("Il footer copyright non è visibile al bordo inferiore.");
  }
  if (!metrics.href.includes("youtube.com/@AngoloInformatico")) {
    throw new Error("Link copyright non corretto.");
  }
  if (screenshotPath) await page.screenshot({ path: screenshotPath });
  process.stdout.write(JSON.stringify(metrics));
} finally {
  await browser.close();
}
