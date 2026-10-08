import { defineConfig, devices } from "@playwright/test";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const frontendDir = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(frontendDir, "..");
const backendDir = path.join(rootDir, "backend");
const pythonPackages = path.join(rootDir, ".python-packages");
const databasePath = path.join(rootDir, ".tmp", "e2e-panel-studio.db").replaceAll("\\", "/");
const venvPython = path.join(
  rootDir,
  ".venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);
const defaultPython = existsSync(venvPython)
  ? `"${venvPython}"`
  : process.platform === "win32"
    ? "py -3.13"
    : "python3";
const pythonCommand = process.env.E2E_PYTHON ?? defaultPython;
const pythonSearchPaths = existsSync(pythonPackages)
  ? [pythonPackages, backendDir]
  : [backendDir];
const backendPort = Number(process.env.E2E_BACKEND_PORT ?? "18000");
const frontendPort = Number(process.env.E2E_FRONTEND_PORT ?? "15173");
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendUrl = `http://127.0.0.1:${frontendPort}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 45_000,
  expect: { timeout: 12_000 },
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: frontendUrl,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `${pythonCommand} -m uvicorn app.main:app --host 127.0.0.1 --port ${backendPort}`,
      cwd: backendDir,
      env: {
        ...process.env,
        PYTHONPATH: process.env.E2E_PYTHONPATH ?? pythonSearchPaths.join(path.delimiter),
        APP_ENV: "test",
        DATABASE_URL: `sqlite:///${databasePath}`,
        LLM_PROVIDER: "fake",
        FRONTEND_ORIGIN: frontendUrl,
      },
      url: `${backendUrl}/api/v1/health`,
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${frontendPort}`,
      cwd: frontendDir,
      env: {
        ...process.env,
        VITE_API_PROXY_TARGET: backendUrl,
      },
      url: frontendUrl,
      reuseExistingServer: false,
      timeout: 30_000,
    },
  ],
});
