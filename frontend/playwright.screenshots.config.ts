import { defineConfig } from '@playwright/test'
import base from './playwright.config.ts'

// `make screenshots`: images for README and docs, written to docs/images/.
export default defineConfig({
  ...base,
  testDir: 'tests/screenshots',
  workers: 1,
  projects: [{ name: 'screenshots' }],
})
