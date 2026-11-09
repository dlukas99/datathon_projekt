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
  await expect(page.locator('.mosaic')).toHaveAttribute('data-state', 'ready')
  await settle(page)
  await page.screenshot({ path: `${OUT}/naslovnica.png` })
})

test('home mobile', async ({ browser }) => {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    isMobile: true,
    hasTouch: true,
  })
  const page = await context.newPage()
  await page.goto('/')
  await expect(page.locator('.mosaic')).toHaveAttribute('data-state', 'ready')
  await settle(page)
  await page.screenshot({ path: `${OUT}/naslovnica-mobitel.png`, fullPage: true })
  await context.close()
})

test('finder', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('/predlozi?profil=obitelj')
  await page.getByRole('button', { name: 'Dalje' }).click()
  await page.getByLabel('Područje').selectOption({ label: 'Vukovarsko-srijemska županija' })
  await page.getByRole('button', { name: 'Dalje' }).click()
  for (const need of ['Vrtić', 'Osnovna škola']) {
    await page.getByRole('checkbox', { name: need }).check()
  }
  await page.getByRole('checkbox', { name: 'Izvan modeliranih poplavnih područja' }).check()
  await page.waitForTimeout(500)
  await page.screenshot({ path: `${OUT}/predlozi.png` })
  await page.getByRole('button', { name: 'Predloži mjesta' }).click()
  await expect(page.locator('.find-results > li').first()).toBeVisible()
  await page.waitForTimeout(500)
  await page.screenshot({ path: `${OUT}/predlozi-rezultati.png`, fullPage: true })
})

test('report desktop', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto(reportUrl(byId('osijek')))
  await expect(page.getByText('Okolišni pregled')).toBeVisible()
  await settle(page)
  // Each instrument moves to its reading once it has been on screen: show them all first.
  for (const inst of await page.locator('.inst').all()) {
    await inst.scrollIntoViewIfNeeded()
    await page.waitForTimeout(300)
  }
  await page.waitForTimeout(2200)
  await page.evaluate(() => {
    window.scrollTo(0, 0)
  })
  await page.screenshot({ path: `${OUT}/izvjestaj.png`, fullPage: true })
  await page.locator('section[aria-labelledby="env-title"]').screenshot({
    path: `${OUT}/okolis.png`,
    style: '.site-header, .report-guide { position: static !important; }',
  })
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
  await page.goto('/o-alatu#izvori')
  await expect(page.getByRole('heading', { name: 'Adrese i granice' })).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/izvori.png` })
})

// Karta Hrvatske: a click at a known place (the map carries its visible area in data-bounds).
async function clickOnMap(page: Page, lon: number, lat: number) {
  const map = page.locator('.atlas-map')
  await expect(map).toHaveAttribute('data-bounds', /,/)
  const box = await map.boundingBox()
  const [w = 0, s = 0, e = 0, n = 0] = ((await map.getAttribute('data-bounds')) ?? '')
    .split(',')
    .map(Number)
  const merc = (y: number) => Math.log(Math.tan(Math.PI / 4 + (y * Math.PI) / 360))
  if (!box) throw new Error('map not visible')
  await page.mouse.click(
    box.x + ((lon - w) / (e - w)) * box.width,
    box.y + ((merc(n) - merc(lat)) / (merc(n) - merc(s))) * box.height,
  )
}

test('map desktop', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('/karta?sloj=air')
  await expect(page.locator('.atlas-map-wrap')).toHaveAttribute('data-ready', 'true')
  await settle(page)
  await page.locator('.atlas').scrollIntoViewIfNeeded()
  await clickOnMap(page, 18.8047, 45.2883) // Vinkovci, town centre
  await expect(page.locator('.atlas-card h2')).toHaveText('Vinkovci')
  await settle(page)
  await page.addStyleTag({ content: '.site-header { position: static !important; }' })
  await page.screenshot({ path: `${OUT}/karta.png`, fullPage: false })
})

test('map mobile', async ({ browser }) => {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    isMobile: true,
    hasTouch: true,
  })
  const page = await context.newPage()
  await page.goto('/karta')
  await expect(page.locator('.atlas-map-wrap')).toHaveAttribute('data-ready', 'true')
  await page.locator('.atlas-map').scrollIntoViewIfNeeded()
  await settle(page)
  await clickOnMap(page, 15.977, 45.813) // Zagreb, Trg bana Jelačića
  await expect(page.locator('.atlas-card h2')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/karta-mobitel.png` })
  await context.close()
})
