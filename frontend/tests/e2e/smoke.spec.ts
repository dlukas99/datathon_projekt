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
  for (const title of ['Poplave', 'Kvaliteta zraka', 'Zelenilo i hlad', 'Promet u blizini', 'Sunce na krovu']) {
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

test('life score has visible, adjustable weights', async ({ page }) => {
  await page.goto(reportUrl)
  const section = page.locator('#skor')
  await expect(section.getByRole('heading', { name: 'Skor za život' })).toBeVisible()
  await expect(section.getByText(/Najviše (podiže|spušta)/)).toBeVisible()
  const slider = section.getByRole('slider', { name: /Poplave/ })
  await slider.fill('0')
  await expect(page).toHaveURL(/tezine=/)
  await expect(section.getByRole('button', { name: 'Vrati težine profila' })).toBeVisible()
})

test('find a place to live ranks settlements with reasons', async ({ page }) => {
  await page.goto('/predlozi')
  await page.getByLabel('Područje').selectOption({ label: 'Vukovarsko-srijemska županija' })
  await page.getByRole('checkbox', { name: 'Vrtić' }).check()
  await page.getByRole('button', { name: 'Predloži mjesta' }).click()
  const results = page.locator('.find-results > li')
  await expect(results.first()).toBeVisible()
  await expect(results.first().getByText(/Najjače:/)).toBeVisible()
  await results.first().getByRole('link', { name: 'Otvori izvještaj' }).click()
  await expect(page.getByText(/Prikazano je središte naselja/)).toBeVisible()
})

test('listing filters close on a click outside or Escape and are shared by all places', async ({
  page,
}) => {
  await page.goto('/predlozi')
  await page.getByRole('button', { name: 'Predloži mjesta' }).click()
  const cards = page.locator('.find-results > li')
  await expect(cards.nth(1)).toBeVisible()

  const firstButton = cards.nth(0).getByRole('button', { name: 'Pogledaj oglase' })
  await firstButton.click()
  await expect(firstButton).toHaveAttribute('aria-expanded', 'true')
  const firstPanel = cards.nth(0).getByRole('group', { name: 'Pogledaj oglase' })
  await firstPanel.getByLabel('Što').selectOption('flat')
  await firstPanel.getByLabel('Najviša cijena (€)').fill('150000')
  await expect(firstButton).toHaveAttribute('aria-expanded', 'true')
  await expectNoAxeViolations(page)

  // A click on empty space closes the panel and gives focus back to the button.
  await page.getByRole('heading', { level: 1 }).click()
  await expect(firstPanel).toBeHidden()
  await expect(firstButton).toBeFocused()

  // The next place has the same filters; Escape closes it.
  const secondButton = cards.nth(1).getByRole('button', { name: 'Pogledaj oglase' })
  await secondButton.click()
  const secondPanel = cards.nth(1).getByRole('group', { name: 'Pogledaj oglase' })
  await expect(secondPanel.getByLabel('Što')).toHaveValue('flat')
  await expect(secondPanel.getByLabel('Najviša cijena (€)')).toHaveValue('150000')
  await secondPanel.getByLabel('Najviše m²').focus()
  await page.keyboard.press('Escape')
  await expect(secondPanel).toBeHidden()
  await expect(secondButton).toBeFocused()

  // Reopened, the first place still has its filters.
  await firstButton.click()
  await expect(firstPanel.getByLabel('Najviša cijena (€)')).toHaveValue('150000')
})

test('main navigation: order, current page, menu on a phone and the old address', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 800 })
  await page.goto('/')
  const nav = page.getByRole('navigation', { name: 'Glavna navigacija' })
  const menu = nav.getByRole('button', { name: 'Izbornik' })
  await expect(nav.getByRole('link', { name: 'Provjeri adresu' })).toBeHidden()
  await menu.click()
  await expect(menu).toHaveAttribute('aria-expanded', 'true')
  await expect(nav.getByRole('link')).toHaveText([
    'Provjeri adresu',
    'Predloži mjesto',
    'Usporedi',
    'O alatu',
  ])
  await expect(nav.getByRole('link', { name: 'Provjeri adresu' })).toHaveAttribute(
    'aria-current',
    'page',
  )
  await expectNoAxeViolations(page)
  await page.keyboard.press('Escape')
  await expect(menu).toHaveAttribute('aria-expanded', 'false')
  await expect(menu).toBeFocused()

  await menu.click()
  await nav.getByRole('link', { name: 'Predloži mjesto' }).click()
  await expect(page).toHaveURL(/\/predlozi$/)
  await expect(menu).toHaveAttribute('aria-expanded', 'false')
  await expect(page.locator('.eyebrow')).toHaveText('Predloži mjesto za život')
  await expect(page).toHaveTitle(/^Predloži mjesto za život/)

  await page.setViewportSize({ width: 1280, height: 800 })
  await expect(menu).toBeHidden()
  await expect(nav.getByRole('link', { name: 'Predloži mjesto' })).toHaveAttribute(
    'aria-current',
    'page',
  )
  await page.goto(reportUrl)
  await expect(nav.getByRole('link', { name: 'Provjeri adresu' })).toHaveAttribute(
    'aria-current',
    'true',
  )

  // Links to the old address keep working, with their parameters.
  await page.goto('/pronadi?profil=obitelj')
  await expect(page).toHaveURL(/\/predlozi\?profil=obitelj$/)
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Gdje bih mogao živjeti')
})

test('assistant answers from the report', async ({ page }) => {
  await page.goto(reportUrl)
  await page.getByRole('button', { name: 'Je li ova kuća u poplavnom području?' }).click()
  await expect(page.getByText(/Za ovu adresu \(poplave/)).toBeVisible()
})

test('walking route to the nearest place of a kind, from the legend and the daily list', async ({
  page,
}) => {
  await page.goto(reportUrl)
  const chip = page.getByRole('button', { name: /^Ljekarna ·/ })
  await chip.click()
  await expect(chip).toHaveAttribute('aria-pressed', 'true')
  const panel = page.getByRole('group', { name: 'Pješački put' })
  await expect(panel).toContainText(/\d+ min · [\d,]+ k?m pješice/)
  await expect(page.locator('.map-wrap [role="status"]')).toContainText('Pješački put do odredišta')
  await expectNoAxeViolations(page)
  await page.keyboard.press('Escape')
  await expect(panel).toHaveCount(0)
  await expect(chip).toHaveAttribute('aria-pressed', 'false')

  await page.locator('.daily-list').getByRole('button', { name: /Ljekarna/ }).click()
  await expect(panel).toContainText(/\d+ min · [\d,]+ k?m pješice/)
  await expect(panel).toBeFocused()
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
      ['find', '/predlozi', 'Gdje bih mogao živjeti'],
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
