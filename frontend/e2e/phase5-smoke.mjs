import process from "node:process";
import { chromium } from "playwright-core";

const [audioPath, screenshotPath] = process.argv.slice(2);
if (!audioPath || !screenshotPath) {
  throw new Error("Uso: node e2e/phase5-smoke.mjs <audio> <screenshot>");
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

  await page.getByRole("button", { name: "Riconosci", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Riconoscimento musicale" });
  await dialog.locator(".recognition-prerequisites").waitFor({ timeout: 20_000 });
  await dialog.getByText("ATS_FPCALC_BINARY", { exact: true }).waitFor();
  await dialog.getByText("ACOUSTID_API_KEY", { exact: true }).waitFor();
  const startDisabled = await dialog.getByRole("button", { name: "Riconosci traccia", exact: true }).isDisabled();
  if (!startDisabled) throw new Error("Il riconoscimento dovrebbe essere disabilitato senza prerequisiti.");
  await page.screenshot({ path: screenshotPath, fullPage: true });
  await dialog.getByRole("button", { name: "Chiudi", exact: true }).click();

  await page.getByRole("button", { name: "Riconosci traccia 1" }).click();
  const singleDialog = page.getByRole("dialog", { name: "Riconoscimento musicale" });
  await singleDialog.getByText("Traccia 1", { exact: true }).waitFor();
  await singleDialog.locator(".recognition-prerequisites").waitFor();
  if (pageErrors.length) throw new Error(`Errori pagina: ${pageErrors.join(" | ")}`);
  process.stdout.write(JSON.stringify({ global: true, single: true, fallback: "manual" }));
} finally {
  await browser.close();
}
