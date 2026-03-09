import { defineConfig, devices } from '@playwright/test';

// PLAYWRIGHT_BASE_URL   — set in CD to point at the deployed gazette; omit to
//                         use the local Eleventy dev server instead.
// PLAYWRIGHT_FULL_SUITE — set to "true" in CD to add Firefox, WebKit, and
//                         mobile projects alongside Chromium.
// SHARD_INDEX / SHARD_TOTAL — injected by the matrix job in CD so each shard
//                              writes test-result attachments to a unique dir.

const isCI = !!process.env.CI;
const isShard = !!process.env.SHARD_TOTAL;
const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:8080';

export default defineConfig({
  testDir: './src',
  timeout: 30_000,
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,

  reporter: isShard
    ? [['blob', { outputDir: 'blob-report' }]]
    : isCI
      ? [['github'], ['html', { open: 'never' }]]
      : [['html']],

  outputDir: process.env.SHARD_INDEX
    ? `test-results-shard-${process.env.SHARD_INDEX}`
    : 'test-results',

  // Eleventy --serve builds the site and starts a dev server on port 8080.
  // Skip the local server when a remote URL is supplied (CD / deployed mode).
  webServer: process.env.PLAYWRIGHT_BASE_URL
    ? undefined
    : {
        command: 'npm exec nx serve gazette',
        url: 'http://localhost:8080',
        reuseExistingServer: !isCI,
        timeout: 180_000, // Eleventy build can be slow on first run
      },

  use: {
    baseURL,
    trace: 'on-first-retry',
    video: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },

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
