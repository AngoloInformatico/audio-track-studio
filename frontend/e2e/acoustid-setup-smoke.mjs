import process from "node:process";
import { chromium } from "playwright-core";

const [screenshotPath] = process.argv.slice(2);
const edgePath = process.env.ATS_EDGE_PATH
  ?? "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const appUrl = process.env.ATS_E2E_URL ?? "http://127.0.0.1:5173";
const browser = await chromium.launch({ executablePath: edgePath, headless: true });
const pageErrors = [];

try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.goto(appUrl, { waitUntil: "networkidle" });
  await page.getByText("Backend connesso").waitFor({ timeout: 20_000 });
  await page.getByRole("button", { name: "Imposta AcoustID" }).click();
  const dialog = page.getByRole("dialog", { name: "Imposta AcoustID" });
  await dialog.getByText("Chiave API AcoustID").waitFor();
  await dialog.getByText("fpcalc / Chromaprint").waitFor();
  await dialog.getByRole("button", { name: /Scarica e configura Chromaprint/ }).waitFor();
  if (screenshotPath) await page.screenshot({ path: screenshotPath, fullPage: true });
  if (pageErrors.length) throw new Error(`Errori pagina: ${pageErrors.join(" | ")}`);
  process.stdout.write(JSON.stringify({ dialogOpened: true, setupStepsVisible: true }));
} finally {
  await browser.close();
}
