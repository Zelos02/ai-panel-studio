import { defineConfig, devices } from "@playwright/test";
import { fileURLToPath } from "node:url";
import path from "node:path";

const frontendDir = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(frontendDir, "..");
const backendDir = path.join(rootDir, "backend");
const pythonPackages = path.join(rootDir, ".python-packages");
const databasePath = path.join(rootDir, ".tmp", "e2e-panel-studio.db").replaceAll("\\", "/");

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 45_000,
  expect: { timeout: 12_000 },
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "py -3.13 -m uvicorn app.main:app --host 127.0.0.1 --port 8000",
      cwd: backendDir,
      env: {
        ...process.env,
        PYTHONPATH: `${pythonPackages};${backendDir}`,
        APP_ENV: "test",
        DATABASE_URL: `sqlite:///${databasePath}`,
        LLM_PROVIDER: "fake",
        FRONTEND_ORIGIN: "http://127.0.0.1:5173",
      },
      url: "http://127.0.0.1:8000/api/v1/health",
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: "npm run dev -- --host 127.0.0.1",
      cwd: frontendDir,
      url: "http://127.0.0.1:5173",
      reuseExistingServer: false,
      timeout: 30_000,
    },
  ],
});
