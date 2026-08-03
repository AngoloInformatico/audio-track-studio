import { existsSync } from "node:fs";
import { join } from "node:path";
import process from "node:process";
import { chromium } from "playwright-core";

const [audioPath, coverPath, exportDirectory, screenshotPath] = process.argv.slice(2);
if (!audioPath || !coverPath || !exportDirectory || !screenshotPath) {
  throw new Error("Uso: node e2e/phase6-smoke.mjs <audio> <cover> <export-dir> <screenshot>");
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

  await page.getByRole("button", { name: "Modifica metadati traccia 1" }).click();
  const metadata = page.getByRole("dialog", { name: "Metadati e copertina" });
  await metadata.getByLabel("Titolo", { exact: true }).fill("Title Six");
  await metadata.getByLabel("Artista", { exact: true }).fill("Artist Six");
  await metadata.getByLabel("Album", { exact: true }).fill("Album Six");
  await metadata.getByLabel("Album Artist", { exact: true }).fill("Album Artist Six");
  await metadata.getByLabel("Numero traccia", { exact: true }).fill("6");
  await metadata.getByLabel("Numero disco", { exact: true }).fill("2");
  await metadata.getByLabel("Anno / Data", { exact: true }).fill("2026");
  await metadata.getByLabel("Genere", { exact: true }).fill("Electronic");
  await metadata.getByLabel("Compositore", { exact: true }).fill("Composer Six");
  await metadata.getByLabel("Commento", { exact: true }).fill("Phase 6 E2E");
  await metadata.locator(".cover-file-input").setInputFiles(coverPath);
  await metadata.locator(".cover-preview img").waitFor({ timeout: 20_000 });
  await page.screenshot({ path: screenshotPath, fullPage: true });
  await metadata.getByRole("button", { name: "Salva metadati" }).click();
  await metadata.waitFor({ state: "detached" });

  await page.getByRole("button", { name: "Esporta", exact: true }).click();
  const exportDialog = page.getByRole("dialog", { name: "Esporta tracce FLAC" });
  await exportDialog.locator(".path-field input").fill(exportDirectory);
  await exportDialog.getByText("Salva anche cover.*", { exact: true }).click();
  await exportDialog.getByRole("button", { name: "Esporta 1 tracce" }).click();
  await exportDialog.locator(".export-completed").waitFor({ timeout: 60_000 });

  const audioOutput = join(exportDirectory, "01 - Artist Six - Title Six.flac");
  const coverOutput = join(exportDirectory, "cover.jpg");
  if (!existsSync(audioOutput)) throw new Error(`File audio non esportato: ${audioOutput}`);
  if (!existsSync(coverOutput)) throw new Error(`File cover non esportato: ${coverOutput}`);
  if (pageErrors.length) throw new Error(`Errori pagina: ${pageErrors.join(" | ")}`);
  process.stdout.write(JSON.stringify({ metadata: true, cover: true, audioOutput, coverOutput }));
} finally {
  await browser.close();
}
