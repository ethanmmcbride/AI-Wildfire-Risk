import { defineConfig, devices } from "@playwright/test";

const isCI = !!process.env.GITHUB_ACTIONS;
const seededDbPath = "../backend/tests/e2e/e2e_wildfire.db";
const backendPort = 38765;
const frontendPort = 38766;

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  fullyParallel: false,
  forbidOnly: isCI,
  retries: isCI ? 1 : 0,
  workers: 1,
  reporter: isCI ? [["github"], ["html", { open: "never" }]] : [["list"]],
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: `python3 ../backend/tests/e2e/seed_db.py --db-path ${seededDbPath} && TEST_DB_PATH=${seededDbPath} PYTHONPATH=../backend/src python3 -m uvicorn ai_wildfire_tracker.api.server:app --host 127.0.0.1 --port ${backendPort}`,
      url: `http://127.0.0.1:${backendPort}/health`,
      reuseExistingServer: !isCI,
      timeout: 120_000,
      cwd: ".",
    },
    {
      command: `VITE_API_BASE_URL=http://127.0.0.1:${backendPort} npm run dev -- --host 127.0.0.1 --port ${frontendPort}`,
      url: `http://127.0.0.1:${frontendPort}`,
      reuseExistingServer: !isCI,
      timeout: 120_000,
      cwd: ".",
    },
  ],
});
