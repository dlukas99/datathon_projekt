// Dev helper (not part of the test suite): full-page captures of the main screens,
// desktop and phone, light and dark, for design review. Usage:
//   node tests/capture.mjs <out-dir> [base-url]
import { mkdirSync } from 'node:fs'
import { chromium } from '@playwright/test'

const out = process.argv[2] ?? 'capture'
const base = process.argv[3] ?? 'http://localhost:5173'
const only = process.argv[4] ? process.argv[4].split(',') : null
const themes = process.argv[5] ? process.argv[5].split(',') : ['light', 'dark']
mkdirSync(out, { recursive: true })

const report =
  '/izvjestaj?lat=45.288384&lon=18.804602&adresa=' +
  encodeURIComponent('Trg bana Josipa Šokčevića 1, Vinkovci')
const shots = [
  ['home', '/', null],
  ['find', '/predlozi', null],
  ['find3', '/predlozi?korak=3&profil=obitelj&podrucje=' + encodeURIComponent('Osječko-baranjska županija') + '&mora=kindergarten', null],
  ['find4', '/predlozi?korak=4&profil=obitelj&podrucje=' + encodeURIComponent('Osječko-baranjska županija') + '&mora=kindergarten', '.find-results li'],
  ['report', report, 'article'],
  ['map', '/karta', '.atlas-map-wrap[data-ready="true"]'],
  ['compare', '/usporedi', null],
]
const views = [
  ['desktop', { width: 1440, height: 900 }],
  ['mobile', { width: 390, height: 844 }],
]

const browser = await chromium.launch()
for (const theme of themes) {
  for (const [vname, viewport] of views) {
    const ctx = await browser.newContext({ viewport, colorScheme: theme, reducedMotion: 'reduce' })
    const page = await ctx.newPage()
    for (const [name, url, wait] of shots) {
      if (only && !only.includes(name)) continue
      if (!only && theme === 'dark' && name !== 'home' && name !== 'report') continue
      await page.goto(base + url)
      if (wait) await page.waitForSelector(wait, { timeout: 60000 })
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${out}/${name}-${vname}-${theme}.png`, fullPage: name !== 'map' })
    }
    await ctx.close()
  }
}
await browser.close()
console.log('captured to', out)
