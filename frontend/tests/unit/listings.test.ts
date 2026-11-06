import {
  buildIndexOglasiUrl,
  buildNekretnineUrl,
  buildNjuskaloUrl,
  formatThousands,
  type ListingQuery,
  listingLinks,
  parsePositiveInt,
  slugify,
} from '../../src/lib/listings'

const SPLIT_ID = '52eb9db8-6dc1-4ed5-acf7-e1669df05240'
const MALI_LOSINJ_ID = '21a57a53-5e8a-4640-baa1-2428432f253f'
const SPLITSKO_DALMATINSKA_ID = '191f5ede-cf31-4c40-b353-257a9061462e'
const GRAD_ZAGREB_ID = '056b6c84-e6f1-433f-8bdc-9b8dbb86d6fb'

function query(overrides: Partial<ListingQuery> = {}): ListingQuery {
  return {
    settlement: 'Split',
    municipality: 'Split',
    county: 'Splitsko-dalmatinska županija',
    kind: 'flat',
    deal: 'sale',
    priceMax: 50000,
    areaMax: 70,
    ...overrides,
  }
}

function indexUrl(path: string, searchQuery: string): string {
  return `https://www.index.hr/oglasi/nekretnine/${path}?searchQuery=${encodeURIComponent(searchQuery)}`
}

function indexSearch(url: string): Record<string, unknown> {
  const raw = new URL(url).searchParams.get('searchQuery') ?? ''
  return JSON.parse(raw) as Record<string, unknown>
}

describe('test case from the brief: Split, flat, sale, 50000 €, 70 m² (checked in a browser)', () => {
  const q = query()

  test('Njuškalo', () => {
    expect(buildNjuskaloUrl(q).url).toBe(
      'https://www.njuskalo.hr/prodaja-stanova/split?price%5Bmax%5D=50000&livingArea%5Bmax%5D=70',
    )
  })

  test('Index Oglasi carries the city id, without which Index ignores the place', () => {
    expect(buildIndexOglasiUrl(q).url).toBe(
      indexUrl(
        'prodaja-stanova/split/pretraga',
        `{"category":"prodaja-stanova","module":"nekretnine","sortOption":4,"includeCityIds":["${SPLIT_ID}"],"priceTo":"50000","areaTo":"70"}`,
      ),
    )
  })

  test('Nekretnine.hr', () => {
    expect(buildNekretnineUrl(q).url).toBe(
      'https://www.nekretnine.hr/prodaja-stanovi/split/?prezzoMassimo=50000&superficieMassima=70',
    )
  })

  test('every link says what it searches for and needs no note', () => {
    for (const l of listingLinks(q)) {
      expect(l.summary).toBe('Split · stan · kupnja · do 50.000 € · do 70 m²')
      expect(l.usedPlace).toBe('Split')
      expect(l.note).toBeNull()
    }
  })
})

test('rent of a house uses each site’s own categories', () => {
  const q = query({ kind: 'house', deal: 'rent', priceMax: 1500, areaMax: 120 })
  expect(buildNjuskaloUrl(q).url).toBe(
    'https://www.njuskalo.hr/iznajmljivanje-kuca/split?price%5Bmax%5D=1500&livingArea%5Bmax%5D=120',
  )
  expect(buildIndexOglasiUrl(q).url).toBe(
    indexUrl(
      'najam-kuca/split/pretraga',
      `{"category":"najam-kuca","module":"nekretnine","sortOption":4,"includeCityIds":["${SPLIT_ID}"],"priceTo":"1500","areaTo":"120"}`,
    ),
  )
  expect(buildNekretnineUrl(q).url).toBe(
    'https://www.nekretnine.hr/najam-samostojeca-kuce/split/?prezzoMassimo=1500&superficieMassima=120',
  )
  expect(buildNekretnineUrl(query({ kind: 'house' })).url).toContain('/prodaja-samostojeca-kuce/split/')
  expect(buildNjuskaloUrl(query({ kind: 'house' })).url).toContain('/prodaja-kuca/split?')
  expect(buildNjuskaloUrl(query({ deal: 'rent' })).url).toContain('/iznajmljivanje-stanova/split?')
  expect(buildNekretnineUrl(query({ deal: 'rent', priceMax: 800 })).url).toBe(
    'https://www.nekretnine.hr/najam-stanovi/split/?prezzoMassimo=800&superficieMassima=70',
  )
  expect(buildNjuskaloUrl(q).summary).toBe('Split · kuća · najam · do 1.500 € · do 120 m²')
  expect(buildIndexOglasiUrl(q).summary).toBe('Split · kuća · najam · do 1.500 € · do 120 m²')
  // Nekretnine.hr has no general house category, only detached houses.
  expect(buildNekretnineUrl(q).summary).toBe(
    'Split · samostojeća kuća · najam · do 1.500 € · do 120 m²',
  )
})

test('an empty price or area adds no parameter at all', () => {
  const noPrice = query({ priceMax: null })
  expect(buildNjuskaloUrl(noPrice).url).toBe(
    'https://www.njuskalo.hr/prodaja-stanova/split?livingArea%5Bmax%5D=70',
  )
  expect(buildNekretnineUrl(noPrice).url).toBe(
    'https://www.nekretnine.hr/prodaja-stanovi/split/?superficieMassima=70',
  )
  expect(indexSearch(buildIndexOglasiUrl(noPrice).url)).not.toHaveProperty('priceTo')

  const neither = query({ priceMax: null, areaMax: null })
  expect(buildNjuskaloUrl(neither).url).toBe('https://www.njuskalo.hr/prodaja-stanova/split')
  expect(buildNekretnineUrl(neither).url).toBe('https://www.nekretnine.hr/prodaja-stanovi/split/')
  expect(indexSearch(buildIndexOglasiUrl(neither).url)).toEqual({
    category: 'prodaja-stanova',
    module: 'nekretnine',
    sortOption: 4,
    includeCityIds: [SPLIT_ID],
  })
  expect(listingLinks(neither)[0]?.summary).toBe('Split · stan · kupnja')

  const noArea = query({ areaMax: null })
  expect(buildNjuskaloUrl(noArea).url).toBe(
    'https://www.njuskalo.hr/prodaja-stanova/split?price%5Bmax%5D=50000',
  )
  expect(indexSearch(buildIndexOglasiUrl(noArea).url)).not.toHaveProperty('areaTo')
})

test('diacritics become plain letters in place slugs', () => {
  const places: [string, string, string][] = [
    ['Đakovo', 'Osječko-baranjska županija', 'dakovo'],
    ['Šibenik', 'Šibensko-kninska županija', 'sibenik'],
    ['Čakovec', 'Međimurska županija', 'cakovec'],
  ]
  for (const [name, county, slug] of places) {
    const q = query({ settlement: name, municipality: name, county })
    expect(buildNjuskaloUrl(q).url).toContain(`/prodaja-stanova/${slug}?`)
    expect(buildNekretnineUrl(q).url).toContain(`/prodaja-stanovi/${slug}/?`)
    expect(buildNjuskaloUrl(q).note).toBeNull()
  }
})

test('a settlement inside a larger town opens that town: Nerezine → Mali Lošinj', () => {
  const q = query({
    settlement: 'Nerezine',
    municipality: 'Mali Lošinj',
    county: 'Primorsko-goranska županija',
    priceMax: 200000,
    areaMax: 60,
  })
  expect(buildNjuskaloUrl(q).url).toBe(
    'https://www.njuskalo.hr/prodaja-stanova/mali-losinj?price%5Bmax%5D=200000&livingArea%5Bmax%5D=60',
  )
  expect(buildIndexOglasiUrl(q).url).toBe(
    indexUrl(
      'prodaja-stanova/mali-losinj/pretraga',
      `{"category":"prodaja-stanova","module":"nekretnine","sortOption":4,"includeCityIds":["${MALI_LOSINJ_ID}"],"priceTo":"200000","areaTo":"60"}`,
    ),
  )
  expect(buildNekretnineUrl(q).url).toBe(
    'https://www.nekretnine.hr/prodaja-stanovi/mali-losinj/?prezzoMassimo=200000&superficieMassima=60',
  )
  for (const l of listingLinks(q)) {
    expect(l.usedPlace).toBe('Mali Lošinj')
    expect(l.note).toBe('Za mjesto Nerezine otvara se šire područje: Mali Lošinj.')
    expect(l.summary).toBe('Mali Lošinj · stan · kupnja · do 200.000 € · do 60 m²')
  }
})

test('Zagreb: "Grad Zagreb" is the city on Njuškalo and Nekretnine.hr, a county on Index', () => {
  const q = query({ settlement: 'Zagreb', municipality: 'Grad Zagreb', county: 'Grad Zagreb' })
  expect(buildNjuskaloUrl(q).url).toContain('/prodaja-stanova/zagreb?')
  expect(buildNekretnineUrl(q).url).toContain('/prodaja-stanovi/zagreb/?')
  const index = buildIndexOglasiUrl(q)
  expect(index.url).toContain('/prodaja-stanova/grad-zagreb/pretraga?')
  expect(indexSearch(index.url)).toHaveProperty('includeCountyIds', [GRAD_ZAGREB_ID])
  for (const l of listingLinks(q)) {
    expect(l.usedPlace).toBe('Zagreb')
    expect(l.note).toBeNull()
  }
})

test('Istrian bilingual names use the Croatian part: "Pula - Pola" → pula', () => {
  const q = query({ settlement: 'Pula', municipality: 'Pula - Pola', county: 'Istarska županija' })
  expect(buildNjuskaloUrl(q).url).toContain('/prodaja-stanova/pula?')
  expect(buildNekretnineUrl(q).url).toContain('/prodaja-stanovi/pula/?')
  expect(buildIndexOglasiUrl(q).url).toContain('/prodaja-stanova/pula/pretraga?')
  for (const l of listingLinks(q)) {
    expect(l.usedPlace).toBe('Pula')
    expect(l.note).toBeNull()
  }
})

test('a name shared by places in two counties falls back to the county', () => {
  const q = query({ settlement: 'Otok', municipality: 'Otok' })
  expect(buildNjuskaloUrl(q).url).toContain('/prodaja-stanova/splitsko-dalmatinska?')
  expect(buildNekretnineUrl(q).url).toContain('/prodaja-stanovi/splitsko-dalmatinska-zupanija/?')
  const index = buildIndexOglasiUrl(q)
  expect(index.url).toContain('/prodaja-stanova/splitsko-dalmatinska/pretraga?')
  expect(indexSearch(index.url)).toHaveProperty('includeCountyIds', [SPLITSKO_DALMATINSKA_ID])
  for (const l of listingLinks(q)) {
    expect(l.usedPlace).toBe('Splitsko-dalmatinska županija')
    expect(l.note).toBe(
      'Više gradova ili općina zove se Otok, pa se otvara šire područje: Splitsko-dalmatinska županija.',
    )
  }
})

test('Index without a known town id uses the county, then a search without a place', () => {
  const inCounty = query({ settlement: 'Primjer', municipality: 'Nepoznata općina' })
  const county = buildIndexOglasiUrl(inCounty)
  expect(county.url).toContain('/prodaja-stanova/splitsko-dalmatinska/pretraga?')
  expect(indexSearch(county.url)).toHaveProperty('includeCountyIds', [SPLITSKO_DALMATINSKA_ID])
  expect(county.note).toBe(
    'Za mjesto Primjer otvara se šire područje: Splitsko-dalmatinska županija.',
  )

  const nowhere = query({
    settlement: 'Primjer',
    municipality: 'Nepoznata općina',
    county: 'Nepoznata županija',
  })
  const index = buildIndexOglasiUrl(nowhere)
  expect(index.url).toBe(
    indexUrl(
      'prodaja-stanova/pretraga',
      '{"category":"prodaja-stanova","module":"nekretnine","sortOption":4,"priceTo":"50000","areaTo":"70"}',
    ),
  )
  expect(index.usedPlace).toBeNull()
  expect(index.note).toBe('Mjesto odaberite ručno u pretrazi oglasnika.')
  expect(index.summary).toBe('cijela Hrvatska · stan · kupnja · do 50.000 € · do 70 m²')
})

test('without a municipality or county nothing is guessed', () => {
  const q = query({ settlement: 'Primjer', municipality: null, county: null })
  const njuskalo = buildNjuskaloUrl(q)
  expect(njuskalo.url).toBe(
    'https://www.njuskalo.hr/prodaja-stanova?price%5Bmax%5D=50000&livingArea%5Bmax%5D=70',
  )
  expect(njuskalo.note).toBe('Mjesto odaberite ručno u pretrazi oglasnika.')
  const nekretnine = buildNekretnineUrl(q)
  expect(nekretnine.url).toBe('https://www.nekretnine.hr/')
  expect(nekretnine.note).toBe('Mjesto i filtre odaberite ručno na stranici oglasnika.')
})

test('links come in a fixed order', () => {
  expect(listingLinks(query()).map((l) => l.id)).toEqual(['njuskalo', 'index', 'nekretnine'])
})

test('slugify follows the same rules as the Python generator', () => {
  expect(slugify('Mali Lošinj')).toBe('mali-losinj')
  expect(slugify('Ivanić-Grad')).toBe('ivanic-grad')
  expect(slugify('Grad Zagreb')).toBe('grad-zagreb')
  expect(slugify('Murter - Kornati')).toBe('murter-kornati')
  expect(slugify('Splitsko-dalmatinska županija')).toBe('splitsko-dalmatinska-zupanija')
  expect(slugify('  Đurđevac  ')).toBe('durdevac')
  expect(slugify('Sv. Filip i Jakov')).toBe('sv-filip-i-jakov')
})

test('price and area accept whole numbers with Croatian grouping only', () => {
  expect(parsePositiveInt('50000')).toBe(50000)
  expect(parsePositiveInt('50.000')).toBe(50000)
  expect(parsePositiveInt('50 000')).toBe(50000)
  expect(parsePositiveInt(`50${String.fromCharCode(0xa0)}000`)).toBe(50000)
  expect(parsePositiveInt(' 1.250.000 ')).toBe(1250000)
  expect(parsePositiveInt('070')).toBe(70)
  for (const bad of ['', '   ', '0', '-5', '50,5', '1.5', '5.00', 'abc', '50k', '1e5', '5 0']) {
    expect(parsePositiveInt(bad)).toBeNull()
  }
})

test('thousands are grouped with a dot', () => {
  expect(formatThousands(70)).toBe('70')
  expect(formatThousands(1500)).toBe('1.500')
  expect(formatThousands(50000)).toBe('50.000')
  expect(formatThousands(1250000)).toBe('1.250.000')
})
