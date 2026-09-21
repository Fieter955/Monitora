import fs from "node:fs";
import process from "node:process";
import {chromium} from "playwright-core";

const candidates = [
  process.env.BROWSER_PATH,
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
].filter(Boolean);

const executablePath = candidates.find((candidate) => fs.existsSync(candidate));
if (!executablePath) {
  throw new Error("Browser Chromium/Edge tidak ditemukan. Isi BROWSER_PATH untuk menjalankan smoke test.");
}

const baseUrl = process.env.PORTAL_URL ?? "http://localhost:8080";
const username = process.env.PORTAL_USERNAME ?? "admin";
const password = process.env.PORTAL_PASSWORD ?? "admin12345";
const screenshot = process.env.UI_SCREENSHOT;

const browser = await chromium.launch({executablePath, headless: true});
try {
  const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
  page.setDefaultTimeout(20_000);
  await page.goto(`${baseUrl}/login`, {waitUntil: "domcontentloaded"});
  await page.getByLabel("Nama pengguna").fill(username);
  await page.getByLabel("Kata sandi").fill(password);
  await page.getByRole("button", {name: "Masuk", exact: true}).click();
  await page.waitForURL(`${baseUrl}/`);
  await page.getByRole("heading", {name: "Ringkasan Infrastruktur"}).waitFor();
  await page.getByText("Kesehatan perangkat").waitFor();

  await page.goto(`${baseUrl}/peta`, {waitUntil: "domcontentloaded"});
  await page.getByRole("heading", {name: "Pencari Gangguan"}).waitFor();
  await page.getByLabel("Cari perangkat, IP, label, atau ruang").waitFor();
  await page.getByRole("heading", {name: "Lokasi & tindakan"}).waitFor();

  await page.goto(`${baseUrl}/topologi`, {waitUntil: "domcontentloaded"});
  await page.getByRole("heading", {name: "Jalur Koneksi"}).waitFor();
  const topologyPanel = page.getByLabel("Topologi aktif");
  await page.getByRole("button", {name: "Layar penuh"}).click();
  if (!await topologyPanel.evaluate((element) => element.classList.contains("topology-panel-fullscreen"))) {
    throw new Error("Panel topologi tidak masuk ke mode layar penuh.");
  }
  await page.getByRole("button", {name: "Pas ke layar"}).waitFor();
  await page.keyboard.press("Escape");
  if (await topologyPanel.evaluate((element) => element.classList.contains("topology-panel-fullscreen"))) {
    throw new Error("Tombol Escape tidak keluar dari mode layar penuh.");
  }
  await page.getByRole("button", {name: "Layar penuh"}).click();
  await page.getByRole("button", {name: "Keluar layar penuh"}).waitFor();
  await page.getByRole("button", {name: "Pas ke layar"}).click();
  await page.keyboard.press("Escape");
  await page.getByRole("button", {name: "Layar penuh"}).waitFor();

  await page.goto(`${baseUrl}/perangkat`, {waitUntil: "domcontentloaded"});
  await page.getByRole("button", {name: "Tambah perangkat"}).click();
  await page.getByLabel("Nama perangkat").fill("Router ICMP Smoke");
  await page.getByLabel("Jenis").selectOption("router");
  await page.getByLabel("IP atau hostname").fill("192.0.2.1");
  await page.getByRole("button", {name: "Lanjut ke akses"}).click();
  await page.getByLabel("Metode monitoring").selectOption("icmp");
  await page.getByText("Monitoring tanpa SNMP").waitFor();
  if (await page.getByLabel("Versi SNMP").count()) {
    throw new Error("Kolom SNMP masih tampil untuk perangkat ICMP-only.");
  }
  await page.getByRole("button", {name: "Tutup", exact: true}).click();
  const labelLink = page.locator('a[aria-label^="Cetak label"]').first();
  await labelLink.waitFor();
  const labelHref = await labelLink.getAttribute("href");
  await page.goto(`${baseUrl}${labelHref}`, {waitUntil: "domcontentloaded"});
  await page.getByRole("heading", {name: "Label perangkat"}).waitFor();
  await page.getByText("MONITORA · ASET JARINGAN").waitFor();

  if (screenshot) {
    await page.screenshot({path: screenshot, fullPage: true});
  }

  await page.setViewportSize({width: 390, height: 844});
  await page.goto(`${baseUrl}/peta`, {waitUntil: "domcontentloaded"});
  await page.getByRole("button", {name: "Buka navigasi"}).waitFor();
  await page.getByRole("heading", {name: "Pencari Gangguan"}).waitFor();
  console.log("UI smoke test passed: locator, topology, printable label, and mobile navigation are reachable.");
} finally {
  await browser.close();
}
