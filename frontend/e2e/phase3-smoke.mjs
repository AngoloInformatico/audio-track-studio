import process from "node:process";
import { chromium } from "playwright-core";

const [audioPath, destinationPath, screenshotPath] = process.argv.slice(2);
if (!audioPath || !destinationPath || !screenshotPath) {
  throw new Error(
    "Uso: node e2e/phase3-smoke.mjs <audio> <destinazione> <screenshot>",
  );
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

  const waveform = page.locator(".waveform-host");
  const box = await waveform.boundingBox();
  if (!box) throw new Error("Waveform non visibile");
  await waveform.dblclick({ position: { x: Math.floor(box.width * 0.5), y: 90 } });
  await page.waitForFunction(() => document.querySelectorAll(".track-table tbody tr").length === 2);

  const rows = page.locator(".track-table tbody tr");
  const saveMetadata = async (index, artist, title) => {
    const row = rows.nth(index);
    await row.locator(".metadata-cell").nth(0).fill(artist);
    await row.locator(".metadata-cell").nth(1).fill(title);
    const saved = page.waitForResponse(
      (response) => response.request().method() === "PATCH"
        && response.url().includes("/tracks/")
        && response.ok(),
    );
    await page.locator(".tracks-heading h2").click();
    await saved;
    await row.getByText("Modificata").waitFor();
  };
  await saveMetadata(0, "Audio Track Studio", "Prima traccia");
  await saveMetadata(1, "Audio Track Studio", "Seconda traccia");

  await page.getByRole("button", { name: "Esporta", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Esporta tracce FLAC" });
  await dialog.waitFor();
  await dialog.getByLabel("Cartella di destinazione").fill(destinationPath);
  await dialog.getByRole("button", { name: "Esporta 2 tracce" }).click();
  await page.waitForFunction(
    () => document.querySelector(".export-completed, .job-progress.failed, .job-progress.cancelled"),
    undefined,
    { timeout: 60_000 },
  );
  await page.screenshot({ path: screenshotPath, fullPage: true });
  const failure = dialog.locator(".job-progress.failed, .job-progress.cancelled");
  if (await failure.count()) {
    throw new Error(`Job export non completato: ${await failure.innerText()}`);
  }
  await dialog.getByText("2 tracce esportate").waitFor();

  const exportedFiles = await dialog.locator(".exported-files > div").count();
  if (exportedFiles !== 2) {
    throw new Error(`Attesi 2 file esportati, ricevuti ${exportedFiles}`);
  }
  if (pageErrors.length) throw new Error(`Errori pagina: ${pageErrors.join(" | ")}`);
  process.stdout.write(JSON.stringify({ tracks: 2, exportedFiles, status: "completed" }));
} finally {
  await browser.close();
}
