import { listingLinks, njuskaloUrl } from '../../src/lib/listings'

test('verified example: Njuskalo house sale in Bebrina with filters', () => {
  const link = njuskaloUrl({
    place: 'Bebrina',
    municipality: 'Bebrina',
    kind: 'house',
    deal: 'sale',
    priceMax: 90000,
    areaMax: 200,
  })
  expect(link.url).toBe(
    'https://www.njuskalo.hr/prodaja-kuca/bebrina-bebrina?price%5Bmax%5D=90000&livingArea%5Bmax%5D=200',
  )
  expect(link.placeInUrl).toBe(true)
})

test('unknown place falls back to the category page, never a guessed slug', () => {
  const link = njuskaloUrl({
    place: 'Vinkovci',
    municipality: 'Vinkovci',
    kind: 'flat',
    deal: 'rent',
    priceMax: null,
    areaMax: null,
  })
  expect(link.url).toBe('https://www.njuskalo.hr/iznajmljivanje-stanova')
  expect(link.placeInUrl).toBe(false)
})

test('other sites get their fallback links', () => {
  const ids = listingLinks({
    place: 'X',
    municipality: 'Y',
    kind: 'house',
    deal: 'sale',
    priceMax: null,
    areaMax: null,
  }).map((l) => l.id)
  expect(ids).toEqual(['njuskalo', 'index', 'nekretnine'])
})
