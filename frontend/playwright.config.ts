import { defineConfig, devices } from '@playwright/test'

// E2E_BASE_URL points the tests at an already running deployment; otherwise the
// backend (port 8000) and the built frontend (`vite preview`, port 4173) are started.
const external = process.env.E2E_BASE_URL
const baseURL = external ?? 'http://localhost:4173'

export default defineConfig({
  testDir: 'tests/e2e',
  timeout: 90_000,
  expect: { timeout: 30_000 },
  retries: 0,
  workers: 2,
  reporter: [['list']],
  use: { baseURL, trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['Pixel 7'] } },
  ],
  webServer: external
    ? undefined
    : [
        {
          command: 'uv run python -m uvicorn app.main:app --port 8000',
          cwd: '../backend',
          url: 'http://localhost:8000/api/health',
          reuseExistingServer: true,
          timeout: 120_000,
          env: { PYTHONUTF8: '1' },
        },
        {
          command: 'npm run preview',
          url: baseURL,
          reuseExistingServer: true,
          timeout: 60_000,
        },
      ],
})
