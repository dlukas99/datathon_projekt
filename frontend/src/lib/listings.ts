// Links to listing searches. We only build URLs; we never fetch or show listings.
// Site formats: config/listings.json. Index Oglasi location ids and names shared by
// several counties: config/listing_locations.json (backend/ingest/listing_locations.py).
import config from '../../../config/listings.json'
import locations from '../../../config/listing_locations.json'

export type Deal = 'sale' | 'rent'
export type Kind = 'house' | 'flat'
export type ProviderId = 'njuskalo' | 'index' | 'nekretnine'

export interface ListingQuery {
  /** Settlement (naselje) the user is looking at. */
  settlement: string
  /** Its town or municipality as named in the DGU units; null when unknown. */
  municipality: string | null
  county: string | null
  kind: Kind
  deal: Deal
  priceMax: number | null
  areaMax: number | null
}

export interface ListingLink {
  id: ProviderId
  label: string
  url: string
  /** Place the search is limited to; null when the user has to pick it on the site. */
  usedPlace: string | null
  /** What the link searches for, e.g. "Split · stan · kupnja · do 50.000 € · do 70 m²". */
  summary: string
  /** Set when the search covers a wider area than the settlement or needs a manual step. */
  note: string | null
}

interface ProviderConfig {
  label: string
  base: string
  categories: Record<`${Kind}-${Deal}`, { path: string; verified: boolean }>
  params: { price_max: string; area_max: string }
  municipality_slugs?: Partial<Record<string, string>>
  search_defaults?: Record<string, string | number>
  /** Wording for a kind when the site's category is narrower, e.g. detached houses only. */
  kind_labels?: Partial<Record<Kind, string>>
}

interface IndexLocation {
  type: 'city' | 'county'
  id: string
}

interface Area {
  level: 'municipality' | 'county'
  /** Name shown to the user. */
  name: string
  slug: string
}

const providers = config.providers as Record<ProviderId, ProviderConfig>
const indexLocations = locations.index_oglasi as unknown as Partial<Record<string, IndexLocation>>
const ambiguous = new Set<string>(locations.ambiguous_municipalities)

const ISTRIA = 'Istarska županija'
// "Grad Zagreb" is both the city and a county; people know the place as Zagreb.
const DISPLAY_NAMES: Partial<Record<string, string>> = { 'Grad Zagreb': 'Zagreb' }
const KIND_LABEL: Record<Kind, string> = { flat: 'stan', house: 'kuća' }
const DEAL_LABEL: Record<Deal, string> = { sale: 'kupnja', rent: 'najam' }
const FOLD: Partial<Record<string, string>> = { č: 'c', ć: 'c', š: 's', ž: 'z', đ: 'd' }
const WHOLE_COUNTRY = 'cijela Hrvatska'

/**
 * Croatian place name to a URL slug: "Đakovo" → "dakovo", "Mali Lošinj" → "mali-losinj".
 * Same rules as `slugify` in backend/ingest/listing_locations.py.
 */
export function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[čćšžđ]/g, (c) => FOLD[c] ?? c)
    .normalize('NFKD')
    .replace(/\p{M}/gu, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

/**
 * Name listing sites use for a town or municipality. Istrian units have official
 * bilingual names ("Pula - Pola"); the sites use the Croatian part. Elsewhere " - " is
 * part of the name ("Murter - Kornati"). Same as `municipality_name` in Python.
 */
function siteName(municipality: string, county: string | null): string {
  if (county === ISTRIA && municipality.includes(' - ')) {
    return municipality.split(' - ')[0] ?? municipality
  }
  return municipality
}

function displayName(municipality: string, county: string | null): string {
  return DISPLAY_NAMES[municipality] ?? siteName(municipality, county)
}

/**
 * A price or area typed by the user as a positive whole number: "50000", "50.000" and
 * "50 000" give 50000. Anything else (empty, zero, decimals, text) gives null, and the
 * filter is then left out of the link.
 */
export function parsePositiveInt(raw: string): number | null {
  // \s also covers the no-break spaces that copied numbers often contain.
  const s = raw.trim().replace(/\s/g, ' ')
  let digits: string
  if (/^\d+$/.test(s)) digits = s
  else if (/^\d{1,3}([. ]\d{3})+$/.test(s)) digits = s.replace(/[. ]/g, '')
  else return null
  const n = Number(digits)
  return Number.isSafeInteger(n) && n > 0 ? n : null
}

/** 50000 → "50.000" (Croatian grouping, independent of the browser locale). */
export function formatThousands(n: number): string {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}

function municipalityArea(q: ListingQuery, p: ProviderConfig): Area | null {
  const m = q.municipality
  // One slug cannot tell apart places with the same name in different counties.
  if (!m || ambiguous.has(m)) return null
  return {
    level: 'municipality',
    name: displayName(m, q.county),
    slug: p.municipality_slugs?.[m] ?? slugify(siteName(m, q.county)),
  }
}

/** Njuškalo and Index use "splitsko-dalmatinska", Nekretnine.hr "splitsko-dalmatinska-zupanija". */
function countyArea(q: ListingQuery, withSuffix: boolean): Area | null {
  if (!q.county) return null
  const name = withSuffix ? q.county : q.county.replace(/ županija$/, '')
  return { level: 'county', name: q.county, slug: slugify(name) }
}

function areaNote(q: ListingQuery, area: Area | null): string | null {
  if (!area) return 'Mjesto odaberite ručno u pretrazi oglasnika.'
  if (area.level === 'county' && q.municipality && ambiguous.has(q.municipality)) {
    const name = siteName(q.municipality, q.county)
    return `Više gradova ili općina zove se ${name}, pa se otvara šire područje: ${area.name}.`
  }
  if (area.level === 'municipality' && [area.name, q.municipality].includes(q.settlement)) {
    return null
  }
  return `Za mjesto ${q.settlement} otvara se šire područje: ${area.name}.`
}

function summary(place: string, q: ListingQuery, p: ProviderConfig): string {
  const parts = [place, p.kind_labels?.[q.kind] ?? KIND_LABEL[q.kind], DEAL_LABEL[q.deal]]
  if (q.priceMax) parts.push(`do ${formatThousands(q.priceMax)} €`)
  if (q.areaMax) parts.push(`do ${formatThousands(q.areaMax)} m²`)
  return parts.join(' · ')
}

function category(p: ProviderConfig, q: ListingQuery): string {
  return p.categories[`${q.kind}-${q.deal}`].path
}

function filters(p: ProviderConfig, q: ListingQuery): [string, string][] {
  const out: [string, string][] = []
  if (q.priceMax) out.push([p.params.price_max, String(q.priceMax)])
  if (q.areaMax) out.push([p.params.area_max, String(q.areaMax)])
  return out
}

function link(id: ProviderId, url: string, area: Area | null, q: ListingQuery): ListingLink {
  return {
    id,
    label: providers[id].label,
    url,
    usedPlace: area?.name ?? null,
    summary: summary(area?.name ?? WHOLE_COUNTRY, q, providers[id]),
    note: areaNote(q, area),
  }
}

/** Njuškalo: the place is a path segment, e.g. /prodaja-stanova/split?price%5Bmax%5D=50000. */
export function buildNjuskaloUrl(q: ListingQuery): ListingLink {
  const p = providers.njuskalo
  const area = municipalityArea(q, p) ?? countyArea(q, false)
  const qs = new URLSearchParams(filters(p, q)).toString()
  const path = area ? `${category(p, q)}/${area.slug}` : category(p, q)
  return link('njuskalo', `${p.base}/${path}${qs ? `?${qs}` : ''}`, area, q)
}

/**
 * Index Oglasi: filters live in a JSON `searchQuery`. Without a location id Index
 * ignores the place in the path, so a place without a known id falls back to its
 * county, and then to a search without a place.
 */
export function buildIndexOglasiUrl(q: ListingQuery): ListingLink {
  const p = providers.index
  const cat = category(p, q)
  const found = [municipalityArea(q, p), countyArea(q, false)]
    .map((area) => (area ? { area, location: indexLocations[area.slug] } : null))
    .find((candidate) => candidate?.location)
  const area = found?.area ?? null
  const search: Record<string, unknown> = { category: cat, ...p.search_defaults }
  if (found?.location) {
    const key = found.location.type === 'city' ? 'includeCityIds' : 'includeCountyIds'
    search[key] = [found.location.id]
  }
  for (const [key, value] of filters(p, q)) search[key] = value
  const path = area ? `${cat}/${area.slug}/pretraga` : `${cat}/pretraga`
  const url = `${p.base}/${path}?searchQuery=${encodeURIComponent(JSON.stringify(search))}`
  return link('index', url, area, q)
}

/** Nekretnine.hr: /prodaja-stanovi/split/?prezzoMassimo=50000 (the trailing slash is needed). */
export function buildNekretnineUrl(q: ListingQuery): ListingLink {
  const p = providers.nekretnine
  const area = municipalityArea(q, p) ?? countyArea(q, true)
  if (!area) {
    return {
      id: 'nekretnine',
      label: p.label,
      url: `${p.base}/`,
      usedPlace: null,
      summary: 'naslovnica oglasnika',
      note: 'Mjesto i filtre odaberite ručno na stranici oglasnika.',
    }
  }
  const qs = new URLSearchParams(filters(p, q)).toString()
  return link('nekretnine', `${p.base}/${category(p, q)}/${area.slug}/${qs ? `?${qs}` : ''}`, area, q)
}

export function listingLinks(q: ListingQuery): ListingLink[] {
  return [buildNjuskaloUrl(q), buildIndexOglasiUrl(q), buildNekretnineUrl(q)]
}
