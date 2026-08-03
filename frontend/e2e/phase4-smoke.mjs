import process from "node:process";
import { chromium } from "playwright-core";

const [audioPath, screenshotPath] = process.argv.slice(2);
if (!audioPath || !screenshotPath) {
  throw new Error("Uso: node e2e/phase4-smoke.mjs <audio> <screenshot>");
}

const edgePath = process.env.ATS_EDGE_PATH
  ?? "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const appUrl = process.env.ATS_E2E_URL ?? "http://127.0.0.1:5173";
const browser = await chromium.launch({ executablePath: edgePath, headless: true });
const pageErrors = [];

try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.goto(appUrl, { waitUntil: "networkidle" });
  await page.getByText("Backend connesso").waitFor({ timeout: 20_000 });
  await page.locator(".global-file-input").setInputFiles(audioPath);
  await page.locator(".track-table tbody tr").waitFor({ timeout: 30_000 });
  await page.locator(".wave-shell.ready").waitFor({ timeout: 30_000 });

  await page.getByRole("button", { name: "Analizza", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Analisi automatica confini" });
  await dialog.waitFor();
  await dialog.locator('input[type="range"]').fill("75");
  await dialog.locator(".analysis-settings select").selectOption("10");
  await dialog.getByRole("button", { name: "Avvia analisi" }).click();
  await dialog.locator(".analysis-results").waitFor({ timeout: 60_000 });

  const suggestions = await dialog.locator(".suggestion-row").count();
  if (suggestions < 2 || suggestions > 3) {
    throw new Error(`Attesi 2-3 suggerimenti, ricevuti ${suggestions}`);
  }
  await page.screenshot({ path: screenshotPath, fullPage: true });
  await dialog.getByRole("button", { name: new RegExp(`Applica selezionati \\(${suggestions}\\)`) }).click();
  await dialog.waitFor({ state: "detached" });
  await page.waitForFunction(
    (expected) => document.querySelectorAll(".track-table tbody tr").length === expected + 1,
    suggestions,
  );

  const tracks = await page.locator(".track-table tbody tr").count();
  const markers = await page.locator(".waveform-host").locator("[part~='region-content']").count();
  if (markers !== suggestions) throw new Error(`Attesi ${suggestions} marker, ricevuti ${markers}`);
  if (pageErrors.length) throw new Error(`Errori pagina: ${pageErrors.join(" | ")}`);
  process.stdout.write(JSON.stringify({ suggestions, tracks, markers, status: "applied" }));
} finally {
  await browser.close();
}
