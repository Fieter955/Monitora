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
  await page.goto(`${baseUrl}/login`, {waitUntil: "networkidle"});
  await page.getByLabel("Nama pengguna").fill(username);
  await page.getByLabel("Kata sandi").fill(password);
  await page.getByRole("button", {name: "Masuk", exact: true}).click();
  await page.waitForURL(`${baseUrl}/`);
  await page.getByRole("heading", {name: "Ringkasan Infrastruktur"}).waitFor();
  await page.getByText("Kesehatan perangkat").waitFor();
  await page.getByText("Server Monitoring", {exact: true}).waitFor();

  if (screenshot) {
    await page.screenshot({path: screenshot, fullPage: true});
  }

  await page.setViewportSize({width: 390, height: 844});
  await page.reload({waitUntil: "networkidle"});
  await page.getByRole("button", {name: "Buka navigasi"}).waitFor();
  console.log("UI smoke test passed: login, dashboard, and mobile navigation are reachable.");
} finally {
  await browser.close();
}
