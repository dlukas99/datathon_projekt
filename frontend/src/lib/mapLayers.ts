import { plural } from './format'
// Layers of the Croatia map. Classes use the same thresholds and names as the report
// (backend/analysis/environment.py, analysis/score.py); docs/METODOLOGIJA.md, "Karta".
import type { MapRow } from './api'

export type LayerId = 'score' | 'air' | 'flood' | 'needs' | 'transit'

export interface LayerClass {
  label: string
  /** Index into the palette, 0 = weakest. */
  step: number
}

export interface MapLayer {
  id: LayerId
  title: string
  /** One line under the legend: what the colour means. */
  explain: string
  /** Classes from the weakest to the strongest. */
  classes: LayerClass[]
  /** Class index for a settlement, null when there is no value. */
  classOf: (row: MapRow, profile: string) => number | null
  /** Value for sorting the table: higher is better; null sorts last. */
  sortValue: (row: MapRow, profile: string) => number | null
  /** The value as text for the table and the card. */
  text: (row: MapRow, profile: string) => string
}

export const MAP_PROFILES = ['opci', 'obitelj', 'umirovljenik', 'student', 'rad-od-kuce'] as const

const AIR_ORDER = ['visoka', 'umjerena', 'niska', 'vrlo niska']
export const AIR_RATING: Record<string, string> = {
  'vrlo niska': 'Vrlo dobar',
  niska: 'Dobar',
  umjerena: 'Umjeren',
  visoka: 'Loš',
}
const FLOOD_ORDER = ['bad', 'warning', 'good']
export const FLOOD_TEXT: Record<string, string> = {
  bad: 'U modeliranom poplavnom području (10 ili 100 godina)',
  warning: 'Područje od 500 godina ili poplavno područje do 100 m',
  good: 'Izvan modeliranih poplavnih područja',
}
export const FLOOD_SHORT: Record<string, string> = {
  bad: 'u poplavnom području',
  warning: 'blizu poplavnog područja',
  good: 'izvan poplavnih područja',
}
const NO_VALUE = 'nema podataka'

const SCORE_BANDS = [20, 40, 60, 80]
// From analysis/score.py: six departures an hour (every 10 minutes) is a full sub-score;
// one an hour is the "barem jednom na sat" need of Život bez auta.
const FREQUENT = 6
const HOURLY = 1

function scoreOf(row: MapRow, profile: string): number | null {
  return row.scores[profile] ?? null
}

export function scoreClass(score: number | null): number | null {
  if (score === null) return null
  const i = SCORE_BANDS.findIndex((upto) => score < upto)
  return i === -1 ? SCORE_BANDS.length : i
}

export function needsClass(needs: number | null): number | null {
  if (needs === null) return null
  if (needs <= 1) return 0
  if (needs <= 3) return 1
  if (needs <= 5) return 2
  return 3
}

/** 0 no stop within 10 min, 1 stops without a timetable, 2 < 1/h, 3 1–6/h, 4 ≥ 6/h. */
export function transitClass(row: MapRow): number | null {
  if (row.departures !== null) {
    if (row.departures >= FREQUENT) return 4
    if (row.departures >= HOURLY) return 3
    return 2
  }
  if (row.needs === null) return null // walking network was not available
  return row.stops ? 1 : 0
}

export function transitText(row: MapRow): string {
  if (row.departures !== null) {
    const n = Math.max(1, Math.round(row.departures))
    return `do ${String(n)} ${plural(n, 'polaska', 'polaska', 'polazaka')} na sat`
  }
  if (row.needs === null) return NO_VALUE
  return row.stops ? 'stajališta bez voznog reda' : 'nema stajališta do 10 minuta hoda'
}

export const LAYERS: MapLayer[] = [
  {
    id: 'score',
    title: 'Skor za život',
    explain: 'Prosjek podskorova kategorija s težinama odabranog profila (0–100).',
    classes: [
      { label: '0–19', step: 0 },
      { label: '20–39', step: 1 },
      { label: '40–59', step: 2 },
      { label: '60–79', step: 3 },
      { label: '80–100', step: 4 },
    ],
    classOf: (r, p) => scoreClass(scoreOf(r, p)),
    sortValue: (r, p) => scoreOf(r, p),
    text: (r, p) => {
      const s = scoreOf(r, p)
      return s === null ? NO_VALUE : `${String(s)} od 100`
    },
  },
  {
    id: 'air',
    title: 'Kvaliteta zraka',
    explain:
      'Lošija od ocjena za PM2,5 i NO2 prema smjernici WHO-a i granicama EU-a, godišnji prosjek 2024.',
    classes: [
      { label: 'Loš', step: 0 },
      { label: 'Umjeren', step: 1 },
      { label: 'Dobar', step: 3 },
      { label: 'Vrlo dobar', step: 4 },
    ],
    classOf: (r) => (r.air === null ? null : AIR_ORDER.indexOf(r.air)),
    sortValue: (r) => {
      if (r.air === null) return null
      // Within a rating, less PM2.5 first.
      return AIR_ORDER.indexOf(r.air) * 1000 - (r.pm25 ?? 0)
    },
    text: (r) => (r.air === null ? NO_VALUE : (AIR_RATING[r.air] ?? r.air)),
  },
  {
    id: 'flood',
    title: 'Poplave',
    explain: 'Modelirane riječne poplave (JRC) u središtu naselja i u krugu od 100 m.',
    classes: [
      { label: FLOOD_TEXT.bad ?? '', step: 0 },
      { label: FLOOD_TEXT.warning ?? '', step: 2 },
      { label: FLOOD_TEXT.good ?? '', step: 4 },
    ],
    classOf: (r) => (r.flood === null ? null : FLOOD_ORDER.indexOf(r.flood)),
    sortValue: (r) => (r.flood === null ? null : FLOOD_ORDER.indexOf(r.flood)),
    text: (r) => (r.flood === null ? NO_VALUE : (FLOOD_SHORT[r.flood] ?? r.flood)),
  },
  {
    id: 'needs',
    title: 'Usluge pješice',
    explain:
      'Koliko od 7 svakodnevnih potreba (trgovina, ljekarna, liječnik, vrtić, škola, park, prijevoz) je do 15 minuta hoda.',
    classes: [
      { label: '0–1 od 7', step: 0 },
      { label: '2–3 od 7', step: 1 },
      { label: '4–5 od 7', step: 3 },
      { label: '6–7 od 7', step: 4 },
    ],
    classOf: (r) => needsClass(r.needs),
    sortValue: (r) => r.needs,
    text: (r) => (r.needs === null ? NO_VALUE : `${String(r.needs)} od 7`),
  },
  {
    id: 'transit',
    title: 'Javni prijevoz',
    explain:
      'Najviše polazaka na sat radnim danom sa stajališta do 10 minuta hoda (vozni redovi ZET-a, HŽPP-a, Gradskog parkinga Šibenik i Autotroleja).',
    classes: [
      { label: 'Nema stajališta do 10 minuta hoda', step: 0 },
      { label: 'Stajališta bez voznog reda', step: 1 },
      { label: 'Manje od 1 polaska na sat', step: 2 },
      { label: '1 do 6 polazaka na sat', step: 3 },
      { label: '6 i više polazaka na sat', step: 4 },
    ],
    classOf: (r) => transitClass(r),
    sortValue: (r) => {
      const c = transitClass(r)
      return c === null ? null : c * 100 + (r.departures ?? 0)
    },
    text: (r) => transitText(r),
  },
]

export function getLayer(id: string | null): MapLayer {
  return LAYERS.find((l) => l.id === id) ?? (LAYERS[0] as MapLayer)
}

/** Feature-state key under which a layer's class is stored on the map. */
export function stateKey(layer: LayerId, profile: string): string {
  return layer === 'score' ? `score_${profile}` : layer
}

/** All class indices of a settlement, keyed for MapLibre feature state. */
export function featureState(row: MapRow): Record<string, number> {
  const out: Record<string, number> = {}
  for (const layer of LAYERS) {
    const profiles = layer.id === 'score' ? MAP_PROFILES : ['opci']
    for (const p of profiles) {
      const c = layer.classOf(row, p)
      if (c !== null) out[stateKey(layer.id, p)] = layer.classes[c]?.step ?? 0
    }
  }
  return out
}

/**
 * Sequential palettes, weakest to strongest: meadow yellow-green to deep forest green, no
 * red-to-green verdict; grey is "no data".
 */
export const PALETTES: Record<'light' | 'dark', { steps: string[]; none: string }> = {
  light: { steps: ['#eef5c8', '#bfe0a0', '#7dbf72', '#348c4a', '#14552c'], none: '#c6cfc4' },
  dark: { steps: ['#1d3a25', '#2c5e36', '#448f4e', '#8ccf7c', '#dcf2a8'], none: '#2f3b33' },
}

/** Rows sorted by the layer, best first (or worst first); missing values always last. */
export function sortRows(rows: MapRow[], layer: MapLayer, profile: string, bestFirst: boolean) {
  return rows
    .map((row) => ({ row, v: layer.sortValue(row, profile) }))
    .sort((a, b) => {
      if (a.v === null && b.v === null) return a.row.name.localeCompare(b.row.name, 'hr')
      if (a.v === null) return 1
      if (b.v === null) return -1
      const d = bestFirst ? b.v - a.v : a.v - b.v
      return d || (b.row.population ?? 0) - (a.row.population ?? 0)
    })
    .map((x) => x.row)
}

const FOLD: Record<string, string> = { č: 'c', ć: 'c', š: 's', ž: 'z', đ: 'd' }

export function fold(text: string): string {
  return text.toLowerCase().replace(/[čćšžđ]/g, (c) => FOLD[c] ?? c)
}

export function matches(row: MapRow, query: string): boolean {
  const q = fold(query.trim())
  if (!q) return true
  return fold(`${row.name} ${row.municipality} ${row.county}`).includes(q)
}
