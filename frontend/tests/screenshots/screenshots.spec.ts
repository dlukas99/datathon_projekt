import { expect, type Page, test } from '@playwright/test'
import demo from '../../../scripts/demo_addresses.json' with { type: 'json' }

type Demo = (typeof demo.addresses)[number]
const byId = (id: string) => demo.addresses.find((d) => d.id === id) as Demo
const OUT = '../docs/images'

function reportUrl(d: Demo, extra = '') {
  return `/izvjestaj?lat=${String(d.lat)}&lon=${String(d.lon)}&adresa=${encodeURIComponent(d.address)}${extra}`
}

async function settle(page: Page) {
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(2500) // map tiles fade in
}

test.describe.configure({ mode: 'serial' })

test('home', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('/')
  await settle(page)
  await page.screenshot({ path: `${OUT}/naslovnica.png` })
})

test('report desktop', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto(reportUrl(byId('osijek')))
  await expect(page.getByText('Okolišni pregled')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/izvjestaj.png`, fullPage: true })
  await page.locator('.map-wrap').scrollIntoViewIfNeeded()
  await settle(page)
  // The section is taller than the window: keep the sticky header out of the picture.
  await page.addStyleTag({ content: '.site-header { position: static !important; }' })
  await page.locator('section[aria-labelledby="carfree-title"]').screenshot({
    path: `${OUT}/zivot-bez-auta.png`,
  })
})

test('report mobile and dark', async ({ browser }) => {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    colorScheme: 'dark',
    isMobile: true,
    hasTouch: true,
  })
  const page = await context.newPage()
  await page.goto(reportUrl(byId('split'), '&profil=obitelj'))
  await expect(page.getByText('Okolišni pregled')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/izvjestaj-mobitel-tamno.png` })
  await context.close()
})

test('compare', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 })
  const a = byId('vinkovci')
  const b = byId('nijemci')
  await page.goto(
    `/usporedi?a=${String(a.lat)},${String(a.lon)}&la=${encodeURIComponent(a.address)}&b=${String(b.lat)},${String(b.lon)}&lb=${encodeURIComponent(b.address)}`,
  )
  await expect(page.getByRole('table')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/usporedba.png`, fullPage: true })
})

test('assistant', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto(reportUrl(byId('zagreb')))
  await page.getByRole('button', { name: 'Mogu li ovdje živjeti bez auta?' }).click()
  await expect(page.getByText(/Za ovu adresu \(život bez auta/)).toBeVisible()
  const section = page.locator('section', { has: page.getByRole('heading', { name: 'Pitajte asistenta' }) })
  await section.screenshot({ path: `${OUT}/asistent.png` })
})

test('sources', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('/izvori')
  await expect(page.getByText('Svi izvori')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/izvori.png` })
})
