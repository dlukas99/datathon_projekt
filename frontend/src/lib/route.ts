// Walking routes for the map, from the backend (`GET /api/route`, Valhalla).
//
// Routes are asked for only on a click. The client keeps them in memory, sends at most
// one request per second, cancels a request when another place is chosen and gives up
// after a timeout, so a slow or unavailable router never blocks the page.
import type { Kind } from './api'
import { distanceSpoken, minutesSpoken } from './format'

export interface LatLon {
  lat: number
  lon: number
}

export interface WalkRoute {
  feature: GeoJSON.Feature<GeoJSON.LineString>
  distanceM: number
  minutes: number
  source: string
  retrievedAt: string | null
  kind: Kind
}

export type RouteFailure = 'timeout' | 'not_found' | 'unavailable'

export class RouteError extends Error {
  readonly reason: RouteFailure | 'aborted'

  constructor(reason: RouteFailure | 'aborted') {
    super(`route ${reason}`)
    this.name = 'RouteError'
    this.reason = reason
  }
}

export const ROUTE_PATH = '/api/route'
/** Coordinates are rounded to 5 decimals (about 1 m) for the request and the cache. */
const DECIMALS = 5
const CACHE_LIMIT = 200

function fixed(value: number): string {
  return value.toFixed(DECIMALS)
}

export function routeKey(from: LatLon, to: LatLon): string {
  return `${fixed(from.lat)},${fixed(from.lon)};${fixed(to.lat)},${fixed(to.lon)}`
}

export function routeUrl(from: LatLon, to: LatLon): string {
  const params = new URLSearchParams({
    from_lat: fixed(from.lat),
    from_lon: fixed(from.lon),
    to_lat: fixed(to.lat),
    to_lon: fixed(to.lon),
  })
  return `${ROUTE_PATH}?${params.toString()}`
}

interface RouteResponse {
  type?: unknown
  geometry?: { type?: unknown; coordinates?: unknown }
  properties?: {
    distance_m?: unknown
    walk_minutes?: unknown
    source?: unknown
    retrieved_at?: unknown
    kind?: unknown
  }
}

function isPosition(value: unknown): value is [number, number] {
  return (
    Array.isArray(value) &&
    value.length >= 2 &&
    typeof value[0] === 'number' &&
    typeof value[1] === 'number'
  )
}

/** Checks the answer of `/api/route`; anything unexpected counts as unavailable. */
export function parseRoute(body: unknown): WalkRoute {
  const data = (body ?? {}) as RouteResponse
  const coordinates = data.geometry?.coordinates
  const props = data.properties
  if (
    data.type !== 'Feature' ||
    data.geometry?.type !== 'LineString' ||
    !Array.isArray(coordinates) ||
    coordinates.length < 2 ||
    !coordinates.every(isPosition) ||
    typeof props?.distance_m !== 'number' ||
    typeof props.walk_minutes !== 'number'
  ) {
    throw new RouteError('unavailable')
  }
  const kind = props.kind
  return {
    feature: {
      type: 'Feature',
      geometry: { type: 'LineString', coordinates },
      properties: {},
    },
    distanceM: props.distance_m,
    minutes: props.walk_minutes,
    source: typeof props.source === 'string' ? props.source : 'valhalla',
    retrievedAt: typeof props.retrieved_at === 'string' ? props.retrieved_at : null,
    kind: kind === 'measured' || kind === 'estimate' ? kind : 'modelled',
  }
}

function abortableSleep(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new RouteError('aborted'))
      return
    }
    const onAbort = () => {
      clearTimeout(timer)
      reject(new RouteError('aborted'))
    }
    const timer = setTimeout(() => {
      signal.removeEventListener('abort', onAbort)
      resolve()
    }, ms)
    signal.addEventListener('abort', onAbort, { once: true })
  })
}

export interface RouteClientOptions {
  fetchImpl?: (url: string, init: RequestInit) => Promise<Response>
  /** Smallest gap between two requests; 1 s, as public routing services ask. */
  minIntervalMs?: number
  timeoutMs?: number
  now?: () => number
  sleep?: (ms: number, signal: AbortSignal) => Promise<void>
}

export interface RouteClient {
  /** A route from the cache or the server; rejects with RouteError. */
  get(from: LatLon, to: LatLon, signal?: AbortSignal): Promise<WalkRoute>
  cached(from: LatLon, to: LatLon): WalkRoute | undefined
}

export function createRouteClient(options: RouteClientOptions = {}): RouteClient {
  const fetchImpl = options.fetchImpl ?? ((url, init) => fetch(url, init))
  const minInterval = options.minIntervalMs ?? 1000
  const timeoutMs = options.timeoutMs ?? 8000
  const now = options.now ?? (() => Date.now())
  const sleep = options.sleep ?? abortableSleep
  const cache = new Map<string, WalkRoute>()
  let lastSent = Number.NEGATIVE_INFINITY
  let queue: Promise<void> = Promise.resolve()

  // Requests leave one at a time, at least `minInterval` apart. A request cancelled
  // while it waits gives its turn to the next one without using up a slot.
  function waitTurn(signal: AbortSignal): Promise<void> {
    const turn = queue.then(async () => {
      const wait = lastSent + minInterval - now()
      if (wait > 0) await sleep(wait, signal)
      if (signal.aborted) throw new RouteError('aborted')
      lastSent = now()
    })
    queue = turn.catch(() => undefined)
    return turn
  }

  async function request(url: string, signal: AbortSignal): Promise<WalkRoute> {
    const controller = new AbortController()
    const state = { timedOut: false }
    const timer = setTimeout(() => {
      state.timedOut = true
      controller.abort()
    }, timeoutMs)
    const forward = () => {
      controller.abort()
    }
    signal.addEventListener('abort', forward, { once: true })
    try {
      const response = await fetchImpl(url, {
        signal: controller.signal,
        headers: { Accept: 'application/json' },
      })
      if (response.status === 404) throw new RouteError('not_found')
      if (!response.ok) throw new RouteError('unavailable')
      return parseRoute(await response.json())
    } catch (error) {
      if (state.timedOut) throw new RouteError('timeout')
      if (signal.aborted) throw new RouteError('aborted')
      if (error instanceof RouteError) throw error
      throw new RouteError('unavailable')
    } finally {
      clearTimeout(timer)
      signal.removeEventListener('abort', forward)
    }
  }

  return {
    cached(from, to) {
      return cache.get(routeKey(from, to))
    },
    async get(from, to, signal = new AbortController().signal) {
      const key = routeKey(from, to)
      const hit = cache.get(key)
      if (hit) return hit
      if (signal.aborted) throw new RouteError('aborted')
      await waitTurn(signal)
      const route = await request(routeUrl(from, to), signal)
      if (cache.size >= CACHE_LIMIT) {
        const oldest = cache.keys().next().value
        if (oldest !== undefined) cache.delete(oldest)
      }
      cache.set(key, route)
      return route
    },
  }
}

/** One client for the whole app, so routes stay cached while the page is open. */
export const routeClient = createRouteClient()

export const ROUTE_MESSAGES: Record<RouteFailure, string> = {
  timeout: 'Put trenutačno nije moguće izračunati. Pokušajte ponovno.',
  unavailable: 'Put trenutačno nije moguće izračunati. Pokušajte ponovno.',
  not_found: 'Pješački put do ovog mjesta nije pronađen.',
}

/** Text for the live region: "Pješački put do odredišta …: 31 minuta, 2,4 kilometra." */
export function routeAnnouncement(title: string, minutes: number, metres: number): string {
  return `Pješački put do odredišta ${title}: ${minutesSpoken(minutes)}, ${distanceSpoken(metres)}.`
}

/** Straight-line distance in metres (haversine), for the text when a route fails. */
export function straightDistance(a: LatLon, b: LatLon): number {
  const r = 6371008.8
  const rad = Math.PI / 180
  const dLat = (b.lat - a.lat) * rad
  const dLon = (b.lon - a.lon) * rad
  const h =
    Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLon / 2) ** 2
  return 2 * r * Math.asin(Math.sqrt(h))
}
