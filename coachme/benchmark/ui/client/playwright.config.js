import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30000,
  use: {
    baseURL: "http://127.0.0.1:8765",
    trace: "retain-on-failure",
  },
  webServer: {
    command: ".venv\\Scripts\\python.exe -m coachme.benchmark.ui.e2e_server",
    cwd: "../../../..",
    port: 8765,
    reuseExistingServer: false,
    timeout: 120000,
  },
});
