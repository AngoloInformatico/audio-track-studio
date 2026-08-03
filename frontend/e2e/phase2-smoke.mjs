import process from "node:process";
import { chromium } from "playwright-core";

const [audioPath, screenshotPath] = process.argv.slice(2);
if (!audioPath || !screenshotPath) {
  throw new Error("Uso: node e2e/phase2-smoke.mjs <audio> <screenshot>");
}

const edgePath = process.env.ATS_EDGE_PATH
  ?? "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const browser = await chromium.launch({ executablePath: edgePath, headless: true });
const pageErrors = [];

try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.goto("http://127.0.0.1:5173", { waitUntil: "networkidle" });
  await page.getByText("Backend connesso").waitFor({ timeout: 20_000 });
  await page.locator(".global-file-input").setInputFiles(audioPath);
  await page.locator(".track-table tbody tr").waitFor({ timeout: 30_000 });
  await page.locator(".wave-shell.ready").waitFor({ timeout: 30_000 });

  const initialRows = await page.locator(".track-table tbody tr").count();
  if (initialRows !== 1) throw new Error(`Attesa 1 traccia iniziale, ricevute ${initialRows}`);

  const waveform = page.locator(".waveform-host");
  const box = await waveform.boundingBox();
  if (!box) throw new Error("Waveform non visibile");
  await waveform.dblclick({ position: { x: Math.floor(box.width * 0.55), y: 90 } });
  await page.waitForFunction(() => document.querySelectorAll(".track-table tbody tr").length === 2);

  const secondRow = page.locator(".track-table tbody tr").nth(1);
  await secondRow.locator(".metadata-cell").nth(0).fill("Test Artist");
  await secondRow.locator(".metadata-cell").nth(1).fill("Second Segment");
  await page.locator(".tracks-heading h2").click();
  await secondRow.getByText("Modificata").waitFor();

  const markerContent = page.locator(".waveform-host").locator("[part~='region-content']");
  if (await markerContent.count() !== 1) throw new Error("Marker WaveSurfer non renderizzato");
  const boundaryInput = page.locator(".track-table tbody tr").first().locator(".timestamp-input").nth(1);
  const boundaryBeforeDrag = await boundaryInput.inputValue();
  const marker = page.locator(".waveform-host").locator("[part~='marker']").first();
  const markerBox = await marker.boundingBox();
  if (!markerBox) throw new Error("Marker non trascinabile");
  await page.mouse.move(markerBox.x + 1, markerBox.y + markerBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(markerBox.x + 65, markerBox.y + markerBox.height / 2, { steps: 8 });
  await page.mouse.up();
  await page.waitForFunction(
    (previous) => document.querySelectorAll(".track-table tbody tr")[0]
      ?.querySelectorAll(".timestamp-input")[1]?.value !== previous,
    boundaryBeforeDrag,
  );

  await page.screenshot({ path: screenshotPath, fullPage: true });
  if (pageErrors.length) throw new Error(`Errori pagina: ${pageErrors.join(" | ")}`);
  process.stdout.write(JSON.stringify({ initialRows, finalRows: 2, markers: 1, markerDrag: "saved", metadata: "saved" }));
} finally {
  await browser.close();
}
