import { defineConfig, devices } from "@playwright/test";
import path from "path";

// Defaults avoid common local conflicts (e.g. other dev stacks using 3000/8000).
const webUrl = process.env.PW_WEB_URL ?? "http://127.0.0.1:13001";
const apiBaseUrl = process.env.PW_API_BASE_URL ?? "http://127.0.0.1:18001";
const repoRoot = path.resolve(__dirname, "..", "..");

const web = new URL(webUrl);
const api = new URL(apiBaseUrl);
const webHost = web.hostname || "127.0.0.1";
const apiHost = api.hostname || "127.0.0.1";
const webPort = Number(web.port || "13001");
const apiPort = Number(api.port || "18001");

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: webUrl,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: [
        "conda",
        "run",
        "-n",
        "Atoms_Jerry",
        "--cwd",
        "apps/api",
        "python",
        "-m",
        "app.devserver",
      ].join(" "),
      cwd: repoRoot,
      url: `${apiBaseUrl}/api/health`,
      timeout: 180_000,
      reuseExistingServer: !process.env.CI,
      env: {
        ...process.env,
        ENV: "test",
        TEST_MODE: "true",
        WEB_APP_URL: webUrl,
        DATABASE_URL: "sqlite:///./e2e.db",
        // Ensure deterministic local tests even if the developer has LLM env vars set.
        DEEPSEEK_API_KEY: "",
        DEEPSEEK_API_BASE: "",
        DEEPSEEK_MODEL: "",
        API_HOST: apiHost,
        API_PORT: String(apiPort),
        HOST: apiHost,
        PORT: String(apiPort),
      },
    },
    {
      command: [
        "pnpm",
        "--filter",
        "@atoms/web",
        "dev",
        "--port",
        String(webPort),
        "--hostname",
        webHost,
      ].join(" "),
      cwd: repoRoot,
      url: webUrl,
      timeout: 180_000,
      reuseExistingServer: !process.env.CI,
      env: {
        ...process.env,
        NEXT_PUBLIC_API_BASE_URL: apiBaseUrl,
      },
    },
  ],
});
