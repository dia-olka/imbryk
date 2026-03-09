import { defineConfig, devices } from '@playwright/test';

// PLAYWRIGHT_BASE_URL   — set in CD to point at the deployed app; omit in CI
//                         to use the local webServer instead.
// PLAYWRIGHT_FULL_SUITE — set to "true" in CD to add Firefox, WebKit, and
//                         mobile projects alongside Chromium.
// SHARD_INDEX / SHARD_TOTAL — injected by the matrix job in CD so each shard
//                              writes test-result attachments to a unique dir.

const isCI = !!process.env.CI;
const isShard = !!process.env.SHARD_TOTAL;
const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:4200';

export default defineConfig({
  testDir: './src',
  timeout: 30_000,
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,

  // In shard mode each worker emits a blob that the merge job will combine.
  // In plain CI mode the github reporter posts annotations directly to the
  // workflow log (no JSON parsing needed on the dev's part).
  // Locally, open the HTML report automatically.
  reporter: isShard
    ? [['blob', { outputDir: 'blob-report' }]]
    : isCI
      ? [['github'], ['html', { open: 'never' }]]
      : [['html']],

  // Attach screenshots / traces under a per-shard directory so parallel
  // matrix jobs never overwrite each other's files.
  outputDir: process.env.SHARD_INDEX
    ? `test-results-shard-${process.env.SHARD_INDEX}`
    : 'test-results',

  // Skip the local dev server when a remote URL is supplied (CD mode).
  webServer: process.env.PLAYWRIGHT_BASE_URL
    ? undefined
    : {
        command: 'npm exec nx serve imbryk',
        url: 'http://localhost:4200',
        reuseExistingServer: !isCI,
        timeout: 120_000,
        env: {
          VITE_APP_URL: 'http://localhost:4200',
        },
      },

  use: {
    baseURL,
    trace: 'on-first-retry',
    video: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },

    // Additional devices enabled in CD via PLAYWRIGHT_FULL_SUITE=true.
    // Keeping CI fast (Chromium only) while CD validates across the full
    // browser / device matrix.
    ...(process.env.PLAYWRIGHT_FULL_SUITE === 'true'
      ? [
          { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
          { name: 'webkit', use: { ...devices['Desktop Safari'] } },
          { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
          { name: 'mobile-safari', use: { ...devices['iPhone 13'] } },
        ]
      : []),
  ],
});
