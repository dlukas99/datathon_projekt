// Types mirror backend/app/models.py.

export type Kind = 'measured' | 'modelled' | 'estimate'
export type Status = 'good' | 'warning' | 'bad' | 'no_data' | 'info'
export type Group = 'environment' | 'car_free' | 'daily'

export interface Value {
  key: string
  label: string
  value: number | string | boolean | null
  unit: string | null
  display: string
  source: string
  retrieved_at: string | null
  kind: Kind
  note: string | null
}

export interface Link {
  label: string
  url: string
}

export interface Place {
  category: string
  name: string
  lat: number
  lon: number
  walk_minutes: number | null
  distance_m: number | null
  source: string
  retrieved_at: string | null
  kind: Kind
  detail: string | null
}

export interface ScaleBand {
  upto: number | null
  label: string
  status: Status
}

export interface Scale {
  key: string
  label: string
  unit: string
  value: number
  band: string
  bands: ScaleBand[]
  markers: { value: number; label: string }[]
}

export interface Category {
  id: string
  group: Group
  title: string
  status: Status
  status_label: string
  headline: string
  values: Value[]
  places: Place[]
  notes: string[]
  links: Link[]
  scales?: Scale[]
  subscore?: number | null
}

export interface Location {
  lat: number
  lon: number
  label: string | null
  settlement: string | null
  municipality: string | null
  county: string | null
  population: Value | null
}

export interface SourceInfo {
  id: string
  title: string
  publisher: string
  url: string
  license: string
  retrieved_at: string | null
  data_date: string | null
}

export interface IsochroneFeature {
  type: 'Feature'
  geometry: GeoJSON.Polygon | GeoJSON.MultiPolygon
  properties: { minutes: number }
}

export interface Report {
  location: Location
  generated_at: string
  summary: string[]
  categories: Category[]
  isochrones: { type: 'FeatureCollection'; features: IsochroneFeature[] } | null
  /** Places for the map: all within 15 minutes and the three nearest of each kind. */
  nearby_places: Place[]
  sources: SourceInfo[]
  disclaimer: string
}

export interface Suggestion {
  label: string
  lat: number
  lon: number
  kind: 'address' | 'street' | 'settlement'
  source: string
  // What was not found when a street or settlement is offered instead.
  note?: string | null
}

export interface LiveSource {
  id: string
  ckan_name: string
  title: string
  organization: string
  metadata_modified: string | null
  url: string
}

export interface LiveSources {
  checked_at: string
  available: boolean
  datasets: LiveSource[]
}

export interface AssistantReply {
  answer: string
  facts: { text: string; source: string; retrieved_at: string | null; kind: Kind }[]
  links: Link[]
  mode: 'rules' | 'llm'
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

const GENERIC_ERROR = 'Poslužitelj trenutačno ne odgovara. Pokušajte ponovno za nekoliko trenutaka.'

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = GENERIC_ERROR
    try {
      const body = (await response.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') message = body.detail
    } catch {
      // keep the generic message
    }
    throw new ApiError(message, response.status)
  }
  return (await response.json()) as T
}

async function getJson<T>(
  path: string,
  params: Record<string, string | number>,
  signal?: AbortSignal,
): Promise<T> {
  const query = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]))
  const qs = query.toString()
  return handle<T>(await fetch(qs ? `${path}?${qs}` : path, { signal }))
}

export function fetchSuggestions(q: string, signal?: AbortSignal): Promise<Suggestion[]> {
  return getJson<Suggestion[]>('/api/geocode', { q, limit: 8 }, signal)
}

export function fetchReport(lat: number, lon: number, signal?: AbortSignal): Promise<Report> {
  return getJson<Report>('/api/report', { lat, lon }, signal)
}

export function fetchSources(signal?: AbortSignal): Promise<SourceInfo[]> {
  return getJson<SourceInfo[]>('/api/sources', {}, signal)
}

export function fetchLiveSources(signal?: AbortSignal): Promise<LiveSources> {
  return getJson<LiveSources>('/api/sources/live', {}, signal)
}

export async function askAssistant(
  question: string,
  points: { lat: number; lon: number; label: string | null }[],
): Promise<AssistantReply> {
  const response = await fetch('/api/assistant', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, locations: points }),
  })
  return handle<AssistantReply>(response)
}

export interface FindRequest {
  profile: string
  weights?: Record<string, number> | null
  county: string | null
  size: 'any' | 'village' | 'town' | 'city'
  must: (
    | 'kindergarten'
    | 'school'
    | 'doctor'
    | 'pediatrician'
    | 'pharmacy'
    | 'grocery'
    | 'park'
    | 'transit'
  )[]
  max_air: 'any' | 'niska' | 'umjerena'
  avoid_flood: boolean
  limit: number
}

export interface FindResult {
  code: string
  name: string
  municipality: string
  county: string
  population: number
  lat: number
  lon: number
  score: number | null
  reasons: string[]
  facts: string[]
}

export interface FindResponse {
  matching: number
  searched: number
  criteria: string[]
  results: FindResult[]
  note: string
}

export interface FindOptions {
  counties: string[]
  settlements: number
  min_population: number
  llm: boolean
}

export function fetchFindOptions(signal?: AbortSignal): Promise<FindOptions> {
  return getJson<FindOptions>('/api/find/options', {}, signal)
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return handle<T>(response)
}

export function findPlaces(request: FindRequest): Promise<FindResponse> {
  return postJson<FindResponse>('/api/find', request)
}

export function parseFindQuestion(question: string): Promise<Partial<FindRequest>> {
  return postJson<Partial<FindRequest>>('/api/find/parse', { question })
}

export function geojsonUrl(lat: number, lon: number): string {
  return `/api/report?lat=${String(lat)}&lon=${String(lon)}&format=geojson`
}

// --- Karta Hrvatske (backend/app/map_layer.py) ---------------------------------------

export interface MapRow {
  id: number
  code: string
  name: string
  municipality: string
  county: string
  population: number
  lat: number
  lon: number
  air: string | null
  pm25: number | null
  no2: number | null
  flood: string | null
  tree: number | null
  green: number | null
  needs: number | null
  departures: number | null
  stops: boolean
  scores: Record<string, number | null>
}

export interface MapTable {
  rows: MapRow[]
  min_population: number
  profiles_date: string | null
  sources: Record<string, { title: string; retrieved_at: string | null }[]>
}

export interface PointTag {
  id: string
  title: string
  text: string
  status: Status
}

export interface MapPoint {
  kind: 'settlement' | 'sea' | 'outside'
  message: string | null
  id: number | null
  code: string | null
  name: string | null
  municipality: string | null
  county: string | null
  population: number | null
  profiled: boolean
  populated: boolean
  centre_lat: number | null
  centre_lon: number | null
  centre_km: number | null
  at_point: PointTag[]
}

/** Compact settlement outlines: rings of delta-encoded integers in steps of `step` degrees. */
export interface CompactGeometry {
  step: number
  features: [number, number[][][]][]
}

export function fetchMapGeometry(
  level: 'overview' | 'detail',
  signal?: AbortSignal,
): Promise<CompactGeometry> {
  return getJson<CompactGeometry>(`/api/map/geometry/${level}`, {}, signal)
}

export function fetchMapTable(signal?: AbortSignal): Promise<MapTable> {
  return getJson<MapTable>('/api/map/settlements', {}, signal)
}

export function fetchMapPoint(lat: number, lon: number, signal?: AbortSignal): Promise<MapPoint> {
  return getJson<MapPoint>(
    '/api/map/point',
    { lat: lat.toFixed(6), lon: lon.toFixed(6) },
    signal,
  )
}
