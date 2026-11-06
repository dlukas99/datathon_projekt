import {
  createRouteClient,
  parseRoute,
  routeAnnouncement,
  RouteError,
  routeKey,
  routeUrl,
  straightDistance,
} from '../../src/lib/route'

const HOME = { lat: 45.288186, lon: 18.805681 }
const SCHOOL = { lat: 45.290412, lon: 18.806029 }
const PARK = { lat: 45.2861, lon: 18.8012 }

function routeBody(minutes = 4.2, metres = 310) {
  return {
    type: 'Feature',
    geometry: {
      type: 'LineString',
      coordinates: [
        [18.805681, 45.288186],
        [18.806029, 45.290412],
      ],
    },
    properties: {
      distance_m: metres,
      walk_minutes: minutes,
      walking_speed_kmh: 4.5,
      source: 'valhalla',
      retrieved_at: null,
      kind: 'modelled',
    },
  }
}

function ok(body: unknown = routeBody()): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

test('the request asks the backend for a walking route with rounded coordinates', () => {
  expect(routeUrl({ lat: 45.2881864, lon: 18.8056811 }, SCHOOL)).toBe(
    '/api/route?from_lat=45.28819&from_lon=18.80568&to_lat=45.29041&to_lon=18.80603',
  )
  // the cache key uses the same rounding (5 decimals, about 1 m)
  expect(routeKey({ lat: 45.2881864, lon: 18.8056811 }, SCHOOL)).toBe(
    routeKey({ lat: 45.288186, lon: 18.805681 }, SCHOOL),
  )
  expect(routeKey(HOME, SCHOOL)).not.toBe(routeKey(HOME, PARK))
})

test('a route answer becomes a GeoJSON line with minutes and metres', () => {
  const route = parseRoute(routeBody(31, 2400))
  expect(route.feature.geometry.coordinates).toHaveLength(2)
  expect(route.minutes).toBe(31)
  expect(route.distanceM).toBe(2400)
  expect(route.kind).toBe('modelled')
  expect(() => parseRoute({ type: 'Feature' })).toThrow(RouteError)
  expect(() => parseRoute(null)).toThrow(RouteError)
})

test('routes are cached: the same trip is fetched once', async () => {
  const fetchImpl = vi.fn(() => Promise.resolve(ok()))
  const client = createRouteClient({ fetchImpl, minIntervalMs: 0 })
  const first = await client.get(HOME, SCHOOL)
  const again = await client.get({ lat: 45.2881861, lon: 18.8056809 }, SCHOOL)
  expect(again).toBe(first)
  expect(fetchImpl).toHaveBeenCalledTimes(1)
  expect(client.cached(HOME, SCHOOL)).toBe(first)
  expect(client.cached(HOME, PARK)).toBeUndefined()
})

test('at most one request per second, also when asked at the same time', async () => {
  let clock = 0
  const sentAt: number[] = []
  const client = createRouteClient({
    now: () => clock,
    sleep: (ms) => {
      clock += ms
      return Promise.resolve()
    },
    fetchImpl: () => {
      sentAt.push(clock)
      return Promise.resolve(ok())
    },
  })
  await client.get(HOME, SCHOOL)
  clock += 300
  await Promise.all([client.get(HOME, PARK), client.get(SCHOOL, PARK)])
  expect(sentAt).toEqual([0, 1000, 2000])
})

test('the throttle holds back the second request for a full second', async () => {
  vi.useFakeTimers()
  try {
    const fetchImpl = vi.fn(() => Promise.resolve(ok()))
    const client = createRouteClient({ fetchImpl })
    const first = client.get(HOME, SCHOOL)
    await vi.advanceTimersByTimeAsync(0)
    expect(fetchImpl).toHaveBeenCalledTimes(1)
    const second = client.get(HOME, PARK)
    await vi.advanceTimersByTimeAsync(999)
    expect(fetchImpl).toHaveBeenCalledTimes(1)
    await vi.advanceTimersByTimeAsync(1)
    expect(fetchImpl).toHaveBeenCalledTimes(2)
    await Promise.all([first, second])
  } finally {
    vi.useRealTimers()
  }
})

test('a request cancelled while waiting is never sent and does not use a slot', async () => {
  vi.useFakeTimers()
  try {
    const fetchImpl = vi.fn(() => Promise.resolve(ok()))
    const client = createRouteClient({ fetchImpl })
    await client.get(HOME, SCHOOL)
    const controller = new AbortController()
    const cancelled = client.get(HOME, PARK, controller.signal)
    const expectation = expect(cancelled).rejects.toMatchObject({ reason: 'aborted' })
    controller.abort()
    await expectation
    // the next request waits only for the first one's second, not for the cancelled one
    const next = client.get(SCHOOL, PARK)
    await vi.advanceTimersByTimeAsync(1000)
    await next
    expect(fetchImpl).toHaveBeenCalledTimes(2)
  } finally {
    vi.useRealTimers()
  }
})

test('a slow router times out, and errors are told apart', async () => {
  const hanging = (_url: string, init: RequestInit) =>
    new Promise<Response>((_resolve, reject) => {
      init.signal?.addEventListener('abort', () => {
        reject(new DOMException('aborted', 'AbortError'))
      })
    })
  const slow = createRouteClient({ fetchImpl: hanging, minIntervalMs: 0, timeoutMs: 20 })
  await expect(slow.get(HOME, SCHOOL)).rejects.toMatchObject({ reason: 'timeout' })

  const status = (code: number) =>
    createRouteClient({
      minIntervalMs: 0,
      fetchImpl: () => Promise.resolve(new Response('{}', { status: code })),
    })
  await expect(status(404).get(HOME, SCHOOL)).rejects.toMatchObject({ reason: 'not_found' })
  await expect(status(503).get(HOME, SCHOOL)).rejects.toMatchObject({ reason: 'unavailable' })

  const offline = createRouteClient({
    minIntervalMs: 0,
    fetchImpl: () => Promise.reject(new TypeError('Failed to fetch')),
  })
  await expect(offline.get(HOME, SCHOOL)).rejects.toMatchObject({ reason: 'unavailable' })
  // failures are not cached: the next try asks again
  expect(offline.cached(HOME, SCHOOL)).toBeUndefined()
})

test('the announcement reads naturally in Croatian', () => {
  expect(routeAnnouncement('Dječji vrtić "Velika"', 31, 2400)).toBe(
    'Pješački put do odredišta Dječji vrtić "Velika": 31 minuta, 2,4 kilometra.',
  )
  expect(routeAnnouncement('Park', 0.2, 17)).toBe(
    'Pješački put do odredišta Park: 1 minuta, 20 metara.',
  )
})

test('straight-line distance for the error text', () => {
  // 0.01 degrees of latitude is about 1.11 km
  expect(straightDistance({ lat: 45, lon: 16 }, { lat: 45.01, lon: 16 })).toBeCloseTo(1112, -1)
})
