import { readFileSync } from "node:fs";
import process from "node:process";
import { chromium } from "playwright-core";

const [audioPath, coverPath, screenshotPath] = process.argv.slice(2);
if (!audioPath || !coverPath || !screenshotPath) {
  throw new Error("Uso: node e2e/phase7-smoke.mjs <audio> <cover> <screenshot>");
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
  await metadata.getByLabel("Titolo", { exact: true }).fill("Phase Seven Track");
  await metadata.getByLabel("Artista", { exact: true }).fill("Audio Track Studio");
  await metadata.getByLabel("Album", { exact: true }).fill("Project Roundtrip");
  await metadata.locator(".cover-file-input").setInputFiles(coverPath);
  await metadata.locator(".cover-preview img").waitFor({ timeout: 20_000 });
  await metadata.getByRole("button", { name: "Salva metadati" }).click();
  await metadata.waitFor({ state: "detached" });

  await page.getByRole("button", { name: "Salva", exact: true }).click();
  const saveDialog = page.getByRole("dialog", { name: "Salva progetto" });
  await saveDialog.getByLabel("Nome progetto").fill("Phase 7 Project");
  const autosave = saveDialog.getByRole("checkbox", { name: /Abilita autosave/ });
  if (!await autosave.isChecked()) await autosave.check();
  await saveDialog.getByRole("button", { name: "Salva .atsproject" }).click();
  await saveDialog.waitFor({ state: "detached" });
  await page.getByText("Autosave aggiornato").waitFor({ timeout: 12_000 });

  await page.getByRole("button", { name: "Progetti" }).click();
  const projects = page.getByRole("dialog", { name: "Progetti" });
  const recent = projects.locator(".project-section").filter({ hasText: "PROGETTI RECENTI" });
  const recovery = projects.locator(".project-section").filter({ hasText: "RECOVERY DISPONIBILI" });
  await recent.getByText("Phase 7 Project", { exact: true }).waitFor();
  await recovery.getByText("Phase 7 Project", { exact: true }).waitFor();

  const downloadPromise = page.waitForEvent("download");
  await recent.getByRole("link", { name: "Scarica Phase 7 Project" }).click();
  const download = await downloadPromise;
  const downloadedPath = await download.path();
  if (!downloadedPath) throw new Error("Download .atsproject non disponibile");
  const document = JSON.parse(readFileSync(downloadedPath, "utf8"));
  if (document.schema_version !== 1 || document.tracks?.[0]?.title !== "Phase Seven Track") {
    throw new Error("Contenuto .atsproject incompleto");
  }
  if (!document.covers || Object.keys(document.covers).length !== 1) {
    throw new Error("Cover non incorporata nel progetto");
  }
  if (JSON.stringify(document).includes(audioPath)) {
    throw new Error("Il progetto contiene il percorso locale della sorgente");
  }

  page.once("dialog", (dialog) => void dialog.accept());
  await projects.getByRole("button", { name: /Nuovo progetto/ }).click();
  await projects.waitFor({ state: "detached" });
  await page.getByText("Trascina qui il tuo audio").waitFor();

  await page.getByRole("button", { name: "Progetti" }).click();
  const reopen = page.getByRole("dialog", { name: "Progetti" });
  await reopen.locator(".project-section").filter({ hasText: "PROGETTI RECENTI" })
    .getByRole("button", { name: /Phase 7 Project/ }).click();
  await reopen.getByText("SORGENTE ATTESA").waitFor();
  await reopen.locator(".project-hidden-input").nth(1).setInputFiles(audioPath);
  await reopen.locator(".dialog-footer .primary").click();
  await reopen.waitFor({ state: "detached", timeout: 30_000 });
  const row = page.locator(".track-table tbody tr").first();
  await row.waitFor();
  if (await row.locator(".metadata-cell").nth(0).inputValue() !== "Audio Track Studio") {
    throw new Error("Artista non ripristinato");
  }
  if (await row.locator(".metadata-cell").nth(1).inputValue() !== "Phase Seven Track") {
    throw new Error("Titolo non ripristinato");
  }
  await page.getByRole("button", { name: "Modifica metadati traccia 1" }).click();
  await page.getByRole("dialog", { name: "Metadati e copertina" })
    .locator(".cover-preview img").waitFor();
  await page.screenshot({ path: screenshotPath, fullPage: true });

  if (pageErrors.length) throw new Error(`Errori pagina: ${pageErrors.join(" | ")}`);
  process.stdout.write(JSON.stringify({
    projectSaved: true,
    recoveryFound: true,
    downloadVerified: true,
    sourceRelinked: true,
    metadataRestored: true,
    coverRestored: true,
  }));
} finally {
  await browser.close();
}
