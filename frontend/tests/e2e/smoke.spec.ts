import AxeBuilder from '@axe-core/playwright'
import { expect, type Page, test } from '@playwright/test'
import demo from '../../../scripts/demo_addresses.json' with { type: 'json' }

const WCAG_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']

type Demo = (typeof demo.addresses)[number]
const first = demo.addresses[0] as Demo
const second = demo.addresses[1] as Demo
const reportUrl = `/izvjestaj?lat=${String(first.lat)}&lon=${String(first.lon)}&adresa=${encodeURIComponent(first.address)}`
const compareUrl = `/usporedi?a=${String(first.lat)},${String(first.lon)}&la=${encodeURIComponent(first.address)}&b=${String(second.lat)},${String(second.lon)}&lb=${encodeURIComponent(second.address)}`

async function expectNoAxeViolations(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(WCAG_TAGS)
    // MapLibre draws the map on a canvas; its text equivalent is checked separately.
    .exclude('.maplibregl-canvas')
    .analyze()
  expect(results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(' ')).join(', ')}`)).toEqual([])
}

test('main flow: search an address and read the report, environment first', async ({ page }) => {
  await page.goto('/')
  const search = page.getByRole('combobox', { name: 'Adresa ili naselje' })
  await search.fill('Franje Kuhača 9, Osijek')
  const option = page.getByRole('option', { name: /Franje Kuhača 9, Osijek/ })
  await expect(option).toBeVisible()
  await search.press('ArrowDown')
  await search.press('Enter')

  await expect(page).toHaveURL(/\/izvjestaj\?/)
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Franje Kuhača 9, Osijek')
  const sections = page.locator('main h2:not(.visually-hidden)')
  await expect(sections.first()).toHaveText('Okolišni pregled')
  for (const title of ['Poplave', 'Kvaliteta zraka', 'Toplina i zelenilo', 'Promet u blizini', 'Sunce na krovu']) {
    await expect(page.getByRole('heading', { level: 3, name: title })).toBeVisible()
  }
  await expect(page.getByRole('heading', { name: 'Život bez auta' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Svakodnevni život' })).toBeVisible()
  await expect(page.getByText(/od 7 svakodnevnih potreba/).first()).toBeVisible()
  // Provenance is one click away on every card.
  const floodCard = page.locator('article[data-category="flood"]')
  await floodCard.getByText('Detalji i izvor').click()
  await expect(floodCard.getByText(/Izvor:/)).toBeVisible()
  await expect(page.getByText(/informativni alat/i).first()).toBeVisible()
})

test('settlement search opens its centre and says so', async ({ page }) => {
  await page.goto('/')
  const search = page.getByRole('combobox', { name: 'Adresa ili naselje' })
  await search.fill('Vinkovci')
  await expect(page.getByRole('option', { name: /Vinkovci.*naselje/ })).toBeVisible()
  await search.press('ArrowDown')
  await search.press('Enter')
  await expect(page.getByText(/Prikazano je središte naselja/)).toBeVisible()
})

test('profile changes order, not values', async ({ page }) => {
  await page.goto(`${reportUrl}&profil=rad-od-kuce`)
  const cards = page.locator('section[aria-labelledby="env-title"] article')
  await expect(cards.first()).toHaveAttribute('data-category', 'noise')
  await expect(cards.first().getByText('Važno za odabrani profil')).toBeVisible()
})

test('assistant answers from the report', async ({ page }) => {
  await page.goto(reportUrl)
  await page.getByRole('button', { name: 'Je li ova kuća u poplavnom području?' }).click()
  await expect(page.getByText(/Za ovu adresu \(poplave/)).toBeVisible()
})

test('comparison shows both addresses side by side', async ({ page }) => {
  await page.goto(compareUrl)
  const table = page.getByRole('table', { name: /Usporedba dviju adresa/ })
  await expect(table).toBeVisible()
  await expect(table.locator('thead th').nth(1)).toContainText(first.address)
  await expect(table.locator('thead th').nth(2)).toContainText(second.address)
  await expect(table.locator('tbody tr[data-category="flood"] td')).toHaveCount(2)
})

test('outside Croatia shows a friendly error', async ({ page }) => {
  await page.goto('/izvjestaj?lat=48.2&lon=16.37')
  await expect(page.getByRole('alert')).toContainText('Lokacija nije u Hrvatskoj')
})

for (const theme of ['light', 'dark'] as const) {
  test.describe(`accessibility (${theme})`, () => {
    test.use({ colorScheme: theme })
    const pages: [string, string, string][] = [
      ['home', '/', 'Kako je živjeti ovdje'],
      ['report', reportUrl, first.address],
      ['compare', compareUrl, 'Usporedba dviju adresa'],
      ['sources', '/izvori', 'Izvori podataka'],
      ['about', '/o-alatu', 'O alatu i metodologiji'],
    ]
    for (const [name, url, heading] of pages) {
      test(`${name} has no axe violations`, async ({ page }) => {
        await page.goto(url)
        await expect(page.getByRole('heading', { level: 1 })).toContainText(heading)
        if (name === 'report') await expect(page.getByText('Okolišni pregled')).toBeVisible()
        if (name === 'compare') await expect(page.getByRole('table')).toBeVisible()
        if (name === 'sources') await expect(page.getByText('Svi izvori')).toBeVisible()
        await expect(page.locator('html')).toHaveAttribute('data-theme', theme)
        await expectNoAxeViolations(page)
      })
    }
  })
}

test('no horizontal scrolling at 320 px', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 })
  for (const url of ['/', reportUrl, compareUrl]) {
    await page.goto(url)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
    if (url !== '/') await page.waitForSelector('article, table')
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    )
    expect(overflow, url).toBeLessThanOrEqual(0)
  }
})
