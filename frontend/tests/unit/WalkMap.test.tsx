import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { useState } from 'react'
import { type WalkFocus, WalkMap } from '../../src/components/WalkMap'
import type { Place, Report } from '../../src/lib/api'
import { placeKey } from '../../src/lib/places'
import { createRouteClient } from '../../src/lib/route'

// jsdom has no WebGL, so MapLibre is replaced by a small fake that records what the
// component asks of the map and lets the test click on it.
const fake = vi.hoisted(() => {
  type Handler = (event?: unknown) => void

  class FakeSource {
    data: unknown
    setData = vi.fn((data: unknown) => {
      this.data = data
      return Promise.resolve()
    })
    constructor(data: unknown) {
      this.data = data
    }
  }

  class FakeMap {
    static instances: FakeMap[] = []
    handlers = new Map<string, Handler[]>()
    sources = new Map<string, FakeSource>()
    layers = new Set<string>()
    paint = new Map<string, unknown>()
    hits: { properties: Record<string, unknown> }[] = []
    canvas = { style: { cursor: '' } }
    constructor() {
      FakeMap.instances.push(this)
      queueMicrotask(() => {
        this.fire('style.load')
        this.fire('load')
      })
    }
    on(type: string, layerOrHandler: string | Handler, handler?: Handler) {
      const key = typeof layerOrHandler === 'string' ? `${type}:${layerOrHandler}` : type
      const fn = typeof layerOrHandler === 'string' ? handler : layerOrHandler
      if (fn) this.handlers.set(key, [...(this.handlers.get(key) ?? []), fn])
      return this
    }
    once(type: string, handler: Handler) {
      const wrapper: Handler = (event) => {
        this.handlers.set(type, (this.handlers.get(type) ?? []).filter((h) => h !== wrapper))
        handler(event)
      }
      return this.on(type, wrapper)
    }
    fire(type: string, event?: unknown) {
      for (const handler of [...(this.handlers.get(type) ?? [])]) handler(event)
    }
    addControl() {
      return this
    }
    addSource(id: string, spec: { data: unknown }) {
      this.sources.set(id, new FakeSource(spec.data))
    }
    getSource(id: string) {
      return this.sources.get(id)
    }
    addLayer(layer: { id: string }) {
      this.layers.add(layer.id)
    }
    getLayer(id: string) {
      return this.layers.has(id) ? { id } : undefined
    }
    setPaintProperty(id: string, name: string, value: unknown) {
      this.paint.set(`${id}.${name}`, value)
    }
    queryRenderedFeatures() {
      return this.hits
    }
    project() {
      return { x: 0, y: 0 }
    }
    getCanvas() {
      return this.canvas
    }
    fitBounds = vi.fn()
    setStyle = vi.fn()
    resize() {
      return this
    }
    remove() {
      return undefined
    }
  }

  class FakePopup {
    static instances: FakePopup[] = []
    content: HTMLElement | null = null
    removed = false
    setLngLat() {
      return this
    }
    setDOMContent(element: HTMLElement) {
      this.content = element
      return this
    }
    addTo() {
      FakePopup.instances.push(this)
      return this
    }
    remove() {
      this.removed = true
      return this
    }
  }

  class FakeMarker {
    static instances: FakeMarker[] = []
    constructor() {
      FakeMarker.instances.push(this)
    }
    handlers = new Map<string, Handler>()
    lngLat = { lng: 0, lat: 0 }
    setLngLat([lng, lat]: [number, number]) {
      this.lngLat = { lng, lat }
      return this
    }
    addTo() {
      return this
    }
    element = document.createElement('div')
    getElement() {
      return this.element
    }
    on(type: string, handler: Handler) {
      this.handlers.set(type, handler)
      return this
    }
    getLngLat() {
      return this.lngLat
    }
  }

  class FakeBounds {
    extend() {
      return this
    }
    isEmpty() {
      return false
    }
  }

  class FakeControl {
    on() {
      return this
    }
  }

  return { FakeMap, FakePopup, FakeMarker, FakeBounds, FakeControl }
})

vi.mock('maplibre-gl', () => ({
  setWorkerUrl: () => undefined,
  Map: fake.FakeMap,
  Popup: fake.FakePopup,
  Marker: fake.FakeMarker,
  LngLatBounds: fake.FakeBounds,
  NavigationControl: fake.FakeControl,
  FullscreenControl: fake.FakeControl,
}))

function place(category: string, name: string, minutes: number, lat: number, lon: number): Place {
  return {
    category,
    name,
    lat,
    lon,
    walk_minutes: minutes,
    distance_m: 1000,
    source: 'test',
    retrieved_at: null,
    kind: 'modelled',
    detail: null,
  }
}

// Made-up places for the test only.
const NEAREST = place('kindergarten', 'Vrtić Prvi', 31, 45.01, 16.01)
const SECOND = place('kindergarten', 'Vrtić Drugi', 35, 45.02, 16.02)
const GROCERY = place('grocery', 'Trgovina Kut', 4, 45.001, 16.001)
const PLACES = [SECOND, GROCERY, NEAREST]

const REPORT: Report = {
  location: {
    lat: 45,
    lon: 16,
    label: null,
    settlement: null,
    municipality: null,
    county: null,
    population: null,
  },
  generated_at: '2026-11-06T00:00:00+00:00',
  summary: [],
  categories: [],
  isochrones: null,
  nearby_places: PLACES,
  sources: [],
  disclaimer: '',
}

function routeResponse(minutes: number, metres: number): Response {
  const body = {
    type: 'Feature',
    geometry: {
      type: 'LineString',
      coordinates: [
        [16, 45],
        [16.01, 45.01],
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
  return new Response(JSON.stringify(body), { status: 200 })
}

function setup(fetchImpl: (url: string) => Promise<Response>) {
  const onPick = vi.fn()
  const fetchSpy = vi.fn(fetchImpl)
  const client = createRouteClient({ fetchImpl: fetchSpy, minIntervalMs: 0 })
  function Harness() {
    const [focus, setFocus] = useState<WalkFocus | null>(null)
    return (
      <WalkMap
        report={REPORT}
        places={PLACES}
        sources={{}}
        onPick={onPick}
        focus={focus}
        onFocus={setFocus}
        client={client}
      />
    )
  }
  render(<Harness />)
  const map = fake.FakeMap.instances.at(-1)
  if (!map) throw new Error('no map')
  return { onPick, fetchSpy, map }
}

function chip(name: RegExp) {
  return screen.getByRole('button', { name })
}

beforeEach(() => {
  fake.FakeMap.instances.length = 0
  fake.FakePopup.instances.length = 0
})

test('clicking a category asks for the route to its nearest place, even beyond 15 minutes', async () => {
  const { fetchSpy, map } = setup(() => Promise.resolve(routeResponse(31, 2400)))
  await waitFor(() => {
    expect(map.layers.has('places')).toBe(true)
  })
  const kindergarten = chip(/^Vrtić/)
  expect(kindergarten).toHaveTextContent('Vrtić – 31 minuta')
  fireEvent.click(kindergarten)
  expect(kindergarten).toHaveAttribute('aria-pressed', 'true')

  await waitFor(() => {
    expect(fetchSpy).toHaveBeenCalledTimes(1)
  })
  expect(fetchSpy.mock.calls[0]?.[0]).toBe(
    '/api/route?from_lat=45.00000&from_lon=16.00000&to_lat=45.01000&to_lon=16.01000',
  )
  const panel = await screen.findByRole('group', { name: 'Pješački put' })
  await within(panel).findByText('2,4 km', { exact: false })
  expect(panel).toHaveTextContent('Najbliži vrtić')
  expect(panel).toHaveTextContent('Vrtić Prvi')
  expect(panel).toHaveTextContent('31 minuta · 2,4 km pješice')
  expect(screen.getByRole('status')).toHaveTextContent(
    'Pješački put do odredišta Vrtić Prvi: 31 minuta, 2,4 kilometra.',
  )
  // the line is drawn, the points of the category are highlighted and the map shows it all
  await waitFor(() => {
    expect(map.sources.get('route')?.data).toMatchObject({ type: 'Feature' })
  })
  expect(JSON.stringify(map.paint.get('places.circle-opacity'))).toContain('kindergarten')
  expect(map.fitBounds).toHaveBeenCalled()

  // "Sljedeći najbliži" goes on to the second nearest
  fireEvent.click(within(panel).getByRole('button', { name: 'Sljedeći najbliži' }))
  await waitFor(() => {
    expect(fetchSpy).toHaveBeenCalledTimes(2)
  })
  expect(fetchSpy.mock.calls[1]?.[0]).toContain('to_lat=45.02000&to_lon=16.02000')
})

test('clicking a point opens its details and does not move the report point', async () => {
  const { onPick, fetchSpy, map } = setup(() => Promise.resolve(routeResponse(4, 150)))
  await waitFor(() => {
    expect(map.layers.has('places')).toBe(true)
  })
  map.hits = [{ properties: { key: placeKey(GROCERY), category: 'grocery' } }]
  act(() => {
    map.fire('click', { point: { x: 10, y: 10 }, lngLat: { lat: 45.5, lng: 16.5 } })
  })
  expect(onPick).not.toHaveBeenCalled()
  const popup = fake.FakePopup.instances.at(-1)
  expect(popup?.content).toHaveTextContent('Trgovina Kut')
  expect(popup?.content).toHaveTextContent('Trgovina namirnicama · 4 minute hoda')

  const show = popup?.content?.querySelector('button')
  expect(show).toHaveTextContent('Prikaži put pješice')
  act(() => {
    show?.click()
  })
  await waitFor(() => {
    expect(fetchSpy).toHaveBeenCalledTimes(1)
  })
  expect(fetchSpy.mock.calls[0]?.[0]).toContain('to_lat=45.00100&to_lon=16.00100')
  expect(popup?.removed).toBe(true)

  // a click or double click away from the points does nothing: the report stays
  map.hits = []
  const away = { point: { x: 300, y: 200 }, lngLat: { lat: 45.5, lng: 16.5 } }
  act(() => {
    map.fire('click', away)
    map.fire('click', away)
    map.fire('dblclick', away)
  })
  expect(onPick).not.toHaveBeenCalled()

  // dragging the marker still moves the report point
  const marker = fake.FakeMarker.instances.at(-1)
  act(() => {
    marker?.setLngLat([16.5, 45.5])
    marker?.handlers.get('dragend')?.({})
  })
  expect(onPick).toHaveBeenCalledExactlyOnceWith(45.5, 16.5)
})

test('Escape removes the route and brings all points back', async () => {
  const { map } = setup(() => Promise.resolve(routeResponse(31, 2400)))
  await waitFor(() => {
    expect(map.layers.has('places')).toBe(true)
  })
  fireEvent.click(chip(/^Vrtić/))
  await screen.findByText('31 minuta', { exact: false, selector: 'strong' })

  fireEvent.keyDown(document, { key: 'Escape' })
  expect(screen.queryByRole('group', { name: 'Pješački put' })).toBeNull()
  expect(chip(/^Vrtić/)).toHaveAttribute('aria-pressed', 'false')
  expect(screen.getByRole('status')).toHaveTextContent('Put je uklonjen.')
  await waitFor(() => {
    expect(map.sources.get('route')?.data).toEqual({ type: 'FeatureCollection', features: [] })
  })
  expect(map.paint.get('places.circle-opacity')).toBe(1)
})

test('a failed route keeps the points highlighted and draws no line', async () => {
  const { map } = setup(() => Promise.resolve(new Response('{}', { status: 503 })))
  await waitFor(() => {
    expect(map.layers.has('places')).toBe(true)
  })
  fireEvent.click(chip(/^Vrtić/))
  const panel = await screen.findByRole('group', { name: 'Pješački put' })
  await within(panel).findByText(/Put trenutačno nije moguće izračunati\. Pokušajte ponovno\./)
  expect(panel).toHaveTextContent('Zračna udaljenost: 1,4 km.')
  expect(within(panel).getByRole('button', { name: 'Pokušaj ponovno' })).toBeInTheDocument()
  expect(map.sources.get('route')?.data).toEqual({ type: 'FeatureCollection', features: [] })
  expect(JSON.stringify(map.paint.get('places.circle-opacity'))).toContain('kindergarten')
})

test('a kind with no places is a disabled button that says why', () => {
  setup(() => Promise.resolve(routeResponse(1, 10)))
  const pediatrician = chip(/^Pedijatar/)
  expect(pediatrician).toBeDisabled()
  expect(pediatrician).toHaveTextContent('nije u blizini')
})
