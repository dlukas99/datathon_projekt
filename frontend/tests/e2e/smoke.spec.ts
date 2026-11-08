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
  for (const title of ['Poplave', 'Kvaliteta zraka', 'Zelenilo i hlad', 'Udaljenost od prometnica', 'Sunce na krovu']) {
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

test('address search reads addresses as people write them and says what it did not find', async ({
  page,
}) => {
  await page.goto('/')
  const search = page.getByRole('combobox', { name: 'Adresa ili naselje' })
  // A school's address without a comma, and Enter before the suggestions appear.
  await search.fill('Ivana Rendića 6 Rijeka')
  await search.press('Enter')
  await expect(page).toHaveURL(/\/izvjestaj\?/)
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Ivana Rendića 6, Rijeka')

  await page.goto('/')
  await search.fill('Gundulićeva 23 A, Zagreb')
  await expect(page.getByRole('option', { name: /Gundulićeva ulica 23A, Zagreb/ })).toBeVisible()
  await search.fill('Ilica 999, Zagreb')
  await expect(page.getByRole('option', { name: /^Ilica, Zagreb/ })).toContainText(
    'Kućni broj 999 nije u registru adresa',
  )
  await expectNoAxeViolations(page)
  await search.fill('Qwxzy 5')
  await expect(page.getByText(/^Nema prijedloga\./)).toBeVisible()
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
  await page.getByRole('button', { name: 'Dalje' }).click()
  await page.getByLabel('Područje').selectOption({ label: 'Vukovarsko-srijemska županija' })
  await page.getByRole('button', { name: 'Dalje' }).click()
  await page.getByRole('checkbox', { name: 'Vrtić' }).check()
  await page.getByRole('button', { name: 'Predloži mjesta' }).click()
  const results = page.locator('.find-results > li')
  await expect(results.first()).toBeVisible()
  await expect(results.first().getByText('Ispunjava uvjete profila')).toBeVisible()
  await results.first().getByRole('link', { name: 'Otvori izvještaj' }).click()
  await expect(page.getByText(/Prikazano je središte naselja/)).toBeVisible()
})

test('the finder walks one question at a time, keeps its answers in the address and goes back', async ({
  page,
}) => {
  await page.goto('/predlozi')
  const steps = page.getByRole('navigation', { name: 'Koraci' })
  await expect(steps.locator('[aria-current="step"]')).toContainText('Tko traži')
  await page.getByRole('radio', { name: /Umirovljenik/ }).check()
  await page.getByRole('button', { name: 'Dalje' }).click()
  await expect(page).toHaveURL(/korak=2/)
  await expect(page).toHaveURL(/profil=umirovljenik/)
  await expect(page.getByRole('heading', { level: 2, name: 'Gdje tražite?' })).toBeFocused()
  await page.getByLabel('Područje').selectOption({ label: 'Osječko-baranjska županija' })
  await page.getByRole('button', { name: 'Dalje' }).click()
  // Weights only under "Napredno".
  await expect(page.getByRole('slider').first()).toBeHidden()
  await page.getByText('Napredno: težine u Skoru za život').click()
  await expect(page.getByRole('slider', { name: /Poplave/ })).toBeVisible()
  await page.goBack()
  await expect(page.getByLabel('Područje')).toHaveValue('Osječko-baranjska županija')
  await steps.getByRole('button', { name: /Tko traži/ }).click()
  await expect(page.getByRole('radio', { name: /Umirovljenik/ })).toBeChecked()
})

test('listing filters close on a click outside or Escape and are shared by all places', async ({
  page,
}) => {
  await page.goto('/predlozi')
  await page.getByRole('button', { name: 'Dalje' }).click()
  await page.getByRole('button', { name: 'Dalje' }).click()
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
    'Karta',
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

// Karta Hrvatske. Clicks go to a known place: the map container carries its visible
// area (data-bounds="w,s,e,n"), and the map is Web Mercator.
const VINKOVCI: [number, number] = [18.8047, 45.2883] // town centre
const FOREST: [number, number] = [17.66, 45.52] // Papuk, outside any village
const SEA: [number, number] = [16.4, 43.4] // between Split and Brač
const ABROAD: [number, number] = [14.505, 46.05] // Ljubljana

async function clickOnMap(page: Page, [lon, lat]: [number, number]) {
  const map = page.locator('.atlas-map')
  await expect(map).toHaveAttribute('data-bounds', /,/)
  await map.scrollIntoViewIfNeeded()
  const box = await map.boundingBox()
  const bounds = (await map.getAttribute('data-bounds')) ?? ''
  const [w = 0, s = 0, e = 0, n = 0] = bounds.split(',').map(Number)
  const merc = (y: number) => Math.log(Math.tan(Math.PI / 4 + (y * Math.PI) / 360))
  if (!box) throw new Error('map not visible')
  await page.mouse.click(
    box.x + ((lon - w) / (e - w)) * box.width,
    box.y + ((merc(n) - merc(lat)) / (merc(n) - merc(s))) * box.height,
  )
}

test('map of Croatia: layers, legend, a click on a town, a forest, the sea and abroad', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('/karta')
  await expect(page).toHaveTitle(/^Karta Hrvatske/)
  const ready = page.locator('.atlas-map-wrap')
  await expect(ready).toHaveAttribute('data-ready', 'true')
  console.log(`map ready in ${String(await ready.getAttribute('data-load-ms'))} ms`)

  // Legend follows the layer, with the report's names, a source and a date.
  const legend = page.locator('.atlas-legend')
  await expect(legend.getByRole('heading')).toHaveText('Skor za život: Općenito')
  await page.getByRole('radio', { name: 'Kvaliteta zraka' }).click()
  await expect(page).toHaveURL(/sloj=air/)
  await expect(page.getByRole('radio', { name: 'Kvaliteta zraka' })).toBeChecked()
  await expect(legend.getByRole('heading')).toHaveText('Kvaliteta zraka')
  await expect(legend.locator('li')).toHaveText([
    'Vrlo dobar',
    'Dobar',
    'Umjeren',
    'Loš',
    'Nema podataka',
  ])
  await expect(legend).toContainText('EEA, karta PM2,5 za 2024. (preuzeto')
  await page.getByRole('radio', { name: 'Skor za život' }).click()
  await expect(page.getByRole('radio', { name: 'Skor za život' })).toBeChecked()

  const card = page.locator('.atlas-card')
  await clickOnMap(page, VINKOVCI)
  await expect(card.locator('h2')).toHaveText('Vinkovci')
  await expect(card).toContainText('stanovnika (Popis 2021.)')
  await expect(card.locator('.atlas-tags li')).toHaveCount(6)
  await expect(card.getByRole('link', { name: 'Otvori puni izvještaj' })).toHaveAttribute(
    'href',
    /\/izvjestaj\?lat=45\.2\d+&lon=18\.8\d+.*tip=karta/,
  )
  await expect(card.getByRole('button', { name: 'Pogledaj oglase' })).toBeVisible()
  await expect(card.locator('h2')).toBeFocused()

  await page.keyboard.press('Escape')
  await expect(card).toHaveCount(0)
  await clickOnMap(page, FOREST)
  await expect(card).toContainText('Odabrana točka je izvan naseljenog dijela; prikazujem naselje')
  await expect(card).toContainText(/središte \d/)
  await expect(card).toContainText('na odabranoj točki')

  await page.keyboard.press('Escape')
  await clickOnMap(page, SEA)
  await expect(card.locator('h2')).toHaveText('Odaberite točku na kopnu.')
  await page.keyboard.press('Escape')
  await clickOnMap(page, ABROAD)
  await expect(card.locator('h2')).toHaveText('Podaci su dostupni samo za Hrvatsku.')
})

test('map of Croatia: the table carries the same data and works with the keyboard', async ({
  page,
}) => {
  await page.goto('/karta?sloj=needs')
  const table = page.locator('.atlas-table')
  await expect(table.locator('tbody tr')).toHaveCount(5)
  await expect(table.locator('thead th').last()).toHaveText('Usluge pješice')
  // Best first: the first row has at least as many needs as the last one shown.
  const values = await table.locator('tbody tr td:last-child').allInnerTexts()
  const n = (t: string) => Number(t.trim().split(' ')[0])
  expect(n(values[0] ?? '')).toBeGreaterThanOrEqual(n(values[values.length - 1] ?? ''))

  await page.getByLabel('Traži naselje').fill('vinkovci')
  // The town and the villages of the town of Vinkovci; diacritics are not needed.
  await expect(table.locator('tbody tr').first()).toContainText('Vinkovci')
  const pick = table.getByRole('button', { name: 'Vinkovci', exact: true })
  await pick.focus()
  await page.keyboard.press('Enter')
  const card = page.locator('.atlas-card')
  await expect(card.locator('h2')).toHaveText('Vinkovci')
  await expect(card.locator('h2')).toBeFocused()
  await expect(card.getByRole('link', { name: 'Otvori puni izvještaj' })).toHaveAttribute(
    'href',
    /tip=naselje/,
  )
  await page.keyboard.press('Escape')
  await expect(card).toHaveCount(0)
  await expect(pick).toBeFocused()
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
  const chip = page.getByRole('button', { name: /^Ljekarna –/ })
  await chip.click()
  await expect(chip).toHaveAttribute('aria-pressed', 'true')
  const panel = page.getByRole('group', { name: 'Pješački put' })
  await expect(panel).toContainText(/(\d+ minut[ae]?|manje od minute) · [\d,]+ k?m pješice/)
  await expect(page.locator('.map-wrap [role="status"]')).toContainText('Pješački put do odredišta')
  await expectNoAxeViolations(page)
  await page.keyboard.press('Escape')
  await expect(panel).toHaveCount(0)
  await expect(chip).toHaveAttribute('aria-pressed', 'false')

  await page.locator('.daily-list').getByRole('button', { name: /Ljekarna/ }).click()
  await expect(panel).toContainText(/(\d+ minut[ae]?|manje od minute) · [\d,]+ k?m pješice/)
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
      ['map', '/karta', 'Istraži kartu Hrvatske'],
    ]
    for (const [name, url, heading] of pages) {
      test(`${name} has no axe violations`, async ({ page }) => {
        await page.goto(url)
        await expect(page.getByRole('heading', { level: 1 })).toContainText(heading)
        if (name === 'report') await expect(page.getByText('Okolišni pregled')).toBeVisible()
        if (name === 'compare') await expect(page.getByRole('table')).toBeVisible()
        if (name === 'sources') await expect(page.getByText('Svi izvori')).toBeVisible()
        if (name === 'map') {
          await expect(page.locator('.atlas-map-wrap')).toHaveAttribute('data-ready', 'true')
          await clickOnMap(page, VINKOVCI)
          await expect(page.locator('.atlas-card h2')).toHaveText('Vinkovci')
        }
        await expect(page.locator('html')).toHaveAttribute('data-theme', theme)
        await expectNoAxeViolations(page)
      })
    }
  })
}

test('no horizontal scrolling at 320 px', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 })
  for (const url of ['/', reportUrl, compareUrl, '/karta']) {
    await page.goto(url)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
    if (url !== '/') await page.waitForSelector('article, table')
    if (url === '/karta') await page.waitForSelector('.atlas-table tbody tr')
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    )
    expect(overflow, url).toBeLessThanOrEqual(0)
  }
})
