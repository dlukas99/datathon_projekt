import type { LiveSources, SourceInfo } from './api'

export type SourceGroupId =
  | 'addresses'
  | 'population'
  | 'environment'
  | 'services'
  | 'transport'
  | 'recycling'
  | 'derived'
  | 'other'

export const SOURCE_GROUPS: { id: SourceGroupId; title: string }[] = [
  { id: 'addresses', title: 'Adrese i granice' },
  { id: 'population', title: 'Stanovništvo' },
  { id: 'environment', title: 'Okoliš' },
  { id: 'services', title: 'Svakodnevne usluge' },
  { id: 'transport', title: 'Prijevoz' },
  { id: 'recycling', title: 'Reciklaža' },
  { id: 'derived', title: 'Izvedeni podaci' },
  { id: 'other', title: 'Ostali izvori' },
]

/** Source id → group, in the order rows are shown. Municipal CKAN datasets go to recycling. */
const GROUP_OF: Record<string, SourceGroupId> = {
  dgu_ad: 'addresses',
  dgu_au: 'addresses',
  dzs_popis: 'population',
  jrc_flood: 'environment',
  eea_pm25: 'environment',
  eea_no2: 'environment',
  eea_stations: 'environment',
  worldcover: 'environment',
  effis: 'environment',
  osm: 'services',
  mzom_vrtici: 'services',
  zg_vrtici: 'services',
  mzom_skole: 'services',
  zg_skole: 'services',
  hzzo_doctor: 'services',
  hzzo_pediatrician: 'services',
  hzzo_ljekarne: 'services',
  mzom_visoka_ucilista: 'services',
  mzom_studijski_programi: 'services',
  osm_facilities: 'services',
  gtfs_zet: 'transport',
  gtfs_hzpp: 'transport',
  autotrolej: 'transport',
  settlement_profiles: 'derived',
  settlement_traffic: 'derived',
}

/** Services and software (PVGIS, Valhalla) are listed apart: they are not datasets. */
export const TOOL_SOURCE_IDS = new Set(['pvgis', 'valhalla'])

/** What a source is used for, where the title alone does not say it. */
export const SOURCE_NOTES: Record<string, string> = {
  osm: 'trgovine, parkovi, igrališta, ulice za hod, velike prometnice i stajališta',
  eea_stations: 'provjera karte zraka',
}

export interface SourceRow extends SourceInfo {
  /** Published on data.gov.hr (the national open data portal). */
  portal: boolean
  /** Last change on the portal, from the live CKAN check (or its last good answer). */
  portalModified: string | null
}

export interface SourceGroup {
  id: SourceGroupId
  title: string
  rows: SourceRow[]
}

export function groupOf(id: string): SourceGroupId {
  if (id.startsWith('ckan:')) return 'recycling'
  return GROUP_OF[id] ?? 'other'
}

const ORDER = Object.keys(GROUP_OF)

/** Data sources grouped by theme; every source lands in a group, none is dropped. */
export function groupSources(sources: SourceInfo[], live?: LiveSources | null): SourceGroup[] {
  const modified = new Map(live?.datasets.map((d) => [d.id, d.metadata_modified]) ?? [])
  const rows: SourceRow[] = sources
    .filter((s) => !TOOL_SOURCE_IDS.has(s.id))
    .map((s) => ({
      ...s,
      portal: s.url.startsWith('https://data.gov.hr/'),
      portalModified: modified.get(s.id) ?? null,
    }))
  const rank = (id: string) => {
    const i = ORDER.indexOf(id)
    return i < 0 ? ORDER.length : i
  }
  return SOURCE_GROUPS.map((g) => ({
    ...g,
    rows: rows
      .filter((r) => groupOf(r.id) === g.id)
      .sort((a, b) => rank(a.id) - rank(b.id) || a.publisher.localeCompare(b.publisher, 'hr')),
  })).filter((g) => g.rows.length > 0)
}
