import { type ReactNode, useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import type { Place, Report } from '../lib/api'
import { wholeMinutes } from '../lib/format'
import { PLACE_COLORS, PLACE_LABELS, placeKey, placeTitle } from '../lib/places'
import type { WalkRoute } from '../lib/route'

// The bundler moves maplibre's module away from its worker file; point to it explicitly.
maplibregl.setWorkerUrl(workerUrl)

type Theme = 'light' | 'dark'

const STYLES: Record<Theme, string> = {
  light: 'https://tiles.openfreemap.org/styles/positron',
  dark: 'https://tiles.openfreemap.org/styles/dark',
}

export const ISOCHRONE_COLORS: Record<number, string> = {
  5: '#1f7a4d',
  10: '#3f8fbf',
  15: '#8a6fbf',
}

// Edge under the route line so it reads over the isochrones: dark on the light map,
// light on the dark one.
const ROUTE_CASING: Record<Theme, string> = { light: '#1d2321', dark: '#f2f4f2' }
const FALLBACK_COLOR = '#666666'

const MAP_LOCALE: Record<string, string> = {
  'Map.Title': 'Karta',
  'NavigationControl.ZoomIn': 'Približi',
  'NavigationControl.ZoomOut': 'Udalji',
  'FullscreenControl.Enter': 'Karta preko cijelog zaslona',
  'FullscreenControl.Exit': 'Izlaz iz prikaza preko cijelog zaslona',
  'Popup.Close': 'Zatvori',
  'AttributionControl.ToggleAttribution': 'Prikaži ili sakrij izvore karte',
  'CooperativeGesturesHandler.WindowsHelpText': 'Za približavanje držite Ctrl i okrenite kotačić',
  'CooperativeGesturesHandler.MacHelpText': 'Za približavanje držite ⌘ i okrenite kotačić',
  'CooperativeGesturesHandler.MobileHelpText': 'Kartu pomičite s dva prsta',
}

// Short, so the attribution stays on one or two lines on a phone.
const ROUTE_ATTRIBUTION =
  'Izokrone i rute: <a href="https://github.com/valhalla/valhalla">Valhalla</a>, ' +
  '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'

const CLICKABLE_LAYERS = ['target', 'places']
// Clicks this close to a point (in pixels) count as a click on the point; easier on touch.
const HIT_TOLERANCE = 8

const EMPTY: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features: [] }

function placesGeojson(places: Place[]): GeoJSON.FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: places.map((p) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [p.lon, p.lat] },
      properties: { key: placeKey(p), category: p.category },
    })),
  }
}

function currentTheme(): Theme {
  return document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'
}

/** The page theme (sun button in the header), followed while the map is open. */
function useDocumentTheme(): Theme {
  const [theme, setTheme] = useState<Theme>(currentTheme)
  useEffect(() => {
    const observer = new MutationObserver(() => {
      setTheme(currentTheme())
    })
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    return () => {
      observer.disconnect()
    }
  }, [])
  return theme
}

/** Sources and layers drawn over the base map, bottom to top. Added on every style load. */
const ISO_OPACITY = 0.14

function reducedMotion(): boolean {
  return typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * The walking circles spread out one after the other, 5, then 10, then 15 minutes, once the
 * map has arrived at the address. With reduced motion they are simply there.
 */
function revealIsochrones(map: maplibregl.Map) {
  const still = reducedMotion()
  ;[5, 10, 15].forEach((minutes, i) => {
    const transition = { duration: still ? 0 : 520, delay: still ? 0 : 160 + i * 380 }
    const fill = `iso-${String(minutes)}`
    const line = `iso-line-${String(minutes)}`
    if (!map.getLayer(fill) || !map.getLayer(line)) return
    map.setPaintProperty(fill, 'fill-opacity-transition', transition)
    map.setPaintProperty(line, 'line-opacity-transition', transition)
    map.setPaintProperty(fill, 'fill-opacity', ISO_OPACITY)
    map.setPaintProperty(line, 'line-opacity', 1)
  })
}

function addOverlays(map: maplibregl.Map, report: Report, hidden: boolean) {
  const iso = report.isochrones
  if (iso) {
    map.addSource('iso', { type: 'geojson', data: iso as GeoJSON.FeatureCollection })
    for (const minutes of [15, 10, 5]) {
      const color = ISOCHRONE_COLORS[minutes] ?? FALLBACK_COLOR
      map.addLayer({
        id: `iso-${String(minutes)}`,
        type: 'fill',
        source: 'iso',
        filter: ['==', ['get', 'minutes'], minutes],
        paint: { 'fill-color': color, 'fill-opacity': hidden ? 0 : ISO_OPACITY },
      })
      map.addLayer({
        id: `iso-line-${String(minutes)}`,
        type: 'line',
        source: 'iso',
        filter: ['==', ['get', 'minutes'], minutes],
        paint: { 'line-color': color, 'line-width': 2, 'line-opacity': hidden ? 0 : 1 },
      })
    }
  }
  // The route is above the isochrones and below the points and the address marker.
  map.addSource('route', { type: 'geojson', data: EMPTY })
  const round = { 'line-join': 'round', 'line-cap': 'round' } as const
  map.addLayer({
    id: 'route-casing',
    type: 'line',
    source: 'route',
    layout: round,
    paint: { 'line-color': ROUTE_CASING.light, 'line-width': 8 },
  })
  map.addLayer({
    id: 'route-line',
    type: 'line',
    source: 'route',
    layout: round,
    paint: { 'line-color': FALLBACK_COLOR, 'line-width': 5 },
  })
  map.addSource('places', { type: 'geojson', data: EMPTY })
  map.addLayer({
    id: 'places',
    type: 'circle',
    source: 'places',
    paint: {
      'circle-radius': 6,
      'circle-color': [
        'match',
        ['get', 'category'],
        ...Object.entries(PLACE_COLORS).flat(),
        FALLBACK_COLOR,
      ] as unknown as maplibregl.ExpressionSpecification,
      'circle-stroke-width': 1.5,
      'circle-stroke-color': '#ffffff',
    },
  })
  map.addSource('target', { type: 'geojson', data: EMPTY })
  map.addLayer({
    id: 'target',
    type: 'circle',
    source: 'target',
    paint: {
      'circle-radius': 9,
      'circle-color': FALLBACK_COLOR,
      'circle-stroke-width': 2.5,
      'circle-stroke-color': '#ffffff',
    },
  })
}

function fitIsochrones(map: maplibregl.Map, report: Report) {
  const bounds = new maplibregl.LngLatBounds()
  for (const f of report.isochrones?.features ?? []) {
    const polygons =
      f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates
    for (const poly of polygons)
      for (const ring of poly) for (const c of ring) bounds.extend(c as maplibregl.LngLatLike)
  }
  // The map arrives at the address from a wider view; reduced motion jumps straight there.
  if (!bounds.isEmpty()) map.fitBounds(bounds, { padding: 24, duration: reducedMotion() ? 0 : 1400 })
}

function fitRoute(map: maplibregl.Map, report: Report, route: WalkRoute) {
  const bounds = new maplibregl.LngLatBounds()
  for (const c of route.feature.geometry.coordinates) bounds.extend(c as maplibregl.LngLatLike)
  bounds.extend([report.location.lon, report.location.lat])
  // Without essential: true, MapLibre skips the animation for prefers-reduced-motion.
  map.fitBounds(bounds, { padding: 56, maxZoom: 17, duration: 600 })
}

function popupContent(place: Place, onShow: () => void): HTMLElement {
  const box = document.createElement('div')
  box.className = 'map-popup'
  const title = document.createElement('strong')
  title.textContent = placeTitle(place)
  const meta = document.createElement('span')
  const minutes =
    place.walk_minutes === null ? '' : ` · ${String(wholeMinutes(place.walk_minutes))} min hoda`
  meta.textContent = `${PLACE_LABELS[place.category] ?? place.category}${minutes}`
  const button = document.createElement('button')
  button.type = 'button'
  button.className = 'button small'
  button.textContent = 'Prikaži put pješice'
  button.addEventListener('click', onShow)
  box.append(title, meta, button)
  return box
}

export function ReportMap({
  report,
  places,
  activeCategory,
  target,
  route,
  onPick,
  onShowRoute,
  children,
}: {
  report: Report
  places: Place[]
  /** Category whose points are highlighted; the others are dimmed. */
  activeCategory: string | null
  /** Destination of the route (enlarged, with a white ring). */
  target: Place | null
  route: WalkRoute | null
  onPick?: (lat: number, lon: number) => void
  onShowRoute: (place: Place) => void
  /** Shown under the map and kept on screen in full-screen mode. */
  children?: ReactNode
}) {
  const frame = useRef<HTMLDivElement>(null)
  const container = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const loadedRef = useRef(false)
  // False while a style is loading: MapLibre throws if layers are changed then.
  const styleReady = useRef(false)
  const appliedTheme = useRef<Theme>('light')
  const placesRef = useRef(places)
  const routeRef = useRef(route)
  const onPickRef = useRef(onPick)
  const onShowRouteRef = useRef(onShowRoute)
  // Increases after every style load, so the effects below draw on the new style.
  const [styleVersion, setStyleVersion] = useState(0)
  const theme = useDocumentTheme()
  const interactive = Boolean(onPick)

  useEffect(() => {
    placesRef.current = places
    routeRef.current = route
    onPickRef.current = onPick
    onShowRouteRef.current = onShowRoute
  })

  useEffect(() => {
    if (!container.current || !frame.current) return
    let map: maplibregl.Map
    appliedTheme.current = currentTheme()
    styleReady.current = false
    try {
      map = new maplibregl.Map({
        container: container.current,
        style: STYLES[appliedTheme.current],
        center: [report.location.lon, report.location.lat],
        zoom: reducedMotion() ? 14.5 : 11,
        attributionControl: { compact: false, customAttribution: ROUTE_ATTRIBUTION },
        cooperativeGestures: true,
        locale: MAP_LOCALE,
      })
    } catch {
      // WebGL is not available (old device or test browser); the text equivalent remains.
      return
    }
    mapRef.current = map
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    const fullscreen = new maplibregl.FullscreenControl({ container: frame.current })
    map.addControl(fullscreen, 'top-right')
    // MapLibre follows the container size itself (trackResize); entering and leaving full
    // screen also changes the frame around it, so resize explicitly then.
    const resize = () => {
      map.resize()
    }
    fullscreen.on('fullscreenstart', resize)
    fullscreen.on('fullscreenend', resize)

    let popup: maplibregl.Popup | null = null
    const closePopup = () => {
      popup?.remove()
      popup = null
    }

    map.on('style.load', () => {
      addOverlays(map, report, !loadedRef.current)
      styleReady.current = true
      setStyleVersion((v) => v + 1)
    })
    map.once('load', () => {
      loadedRef.current = true
      const current = routeRef.current
      if (current) fitRoute(map, report, current)
      else fitIsochrones(map, report)
      if (current || reducedMotion()) {
        revealIsochrones(map)
      } else {
        // After the flight; the timer covers a camera that had nowhere to move.
        const reveal = () => {
          window.clearTimeout(timer)
          revealIsochrones(map)
        }
        const timer = window.setTimeout(reveal, 1800)
        map.once('moveend', reveal)
      }
      for (const id of CLICKABLE_LAYERS) {
        map.on('mouseenter', id, () => {
          map.getCanvas().style.cursor = 'pointer'
        })
        map.on('mouseleave', id, () => {
          map.getCanvas().style.cursor = ''
        })
      }
    })

    // A click on a point opens its details; only a click elsewhere moves the report point.
    map.on('click', (e) => {
      if (!styleReady.current) return
      const { x, y } = e.point
      const layers = CLICKABLE_LAYERS.filter((id) => map.getLayer(id))
      const hits = layers.length
        ? map.queryRenderedFeatures(
            [
              [x - HIT_TOLERANCE, y - HIT_TOLERANCE],
              [x + HIT_TOLERANCE, y + HIT_TOLERANCE],
            ],
            { layers },
          )
        : []
      if (hits.length > 0) {
        // Of the points near the click, the one closest to it.
        let place: Place | undefined
        let best = Infinity
        for (const p of placesRef.current) {
          if (!hits.some((f) => f.properties.key === placeKey(p))) continue
          const at = map.project([p.lon, p.lat])
          const distance = Math.hypot(at.x - x, at.y - y)
          if (distance < best) {
            best = distance
            place = p
          }
        }
        closePopup()
        if (place) {
          popup = new maplibregl.Popup({ offset: 10, maxWidth: '280px' })
            .setLngLat([place.lon, place.lat])
            .setDOMContent(
              popupContent(place, () => {
                closePopup()
                onShowRouteRef.current(place)
              }),
            )
            .addTo(map)
        }
        return
      }
      onPickRef.current?.(e.lngLat.lat, e.lngLat.lng)
    })

    const marker = new maplibregl.Marker({ color: '#15171a', draggable: interactive })
      .setLngLat([report.location.lon, report.location.lat])
      .addTo(map)
    marker.on('dragend', () => {
      const p = marker.getLngLat()
      onPickRef.current?.(p.lat, p.lng)
    })

    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closePopup()
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
      mapRef.current = null
      loadedRef.current = false
      styleReady.current = false
      map.remove()
    }
  }, [report, interactive])

  // The sun button in the header switches the base map without losing the overlays.
  useEffect(() => {
    const map = mapRef.current
    if (!map || appliedTheme.current === theme) return
    appliedTheme.current = theme
    styleReady.current = false
    map.setStyle(STYLES[theme], { diff: false })
  }, [theme])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !styleVersion || !styleReady.current) return
    map.setPaintProperty('route-casing', 'line-color', ROUTE_CASING[theme])
  }, [theme, styleVersion])

  useEffect(() => {
    if (!styleVersion || !styleReady.current) return
    const source = mapRef.current?.getSource<maplibregl.GeoJSONSource>('places')
    void source?.setData(placesGeojson(places))
  }, [places, styleVersion])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !styleVersion || !styleReady.current) return
    const active: maplibregl.ExpressionSpecification = [
      '==',
      ['get', 'category'],
      activeCategory ?? '',
    ]
    const radius: maplibregl.DataDrivenPropertyValueSpecification<number> = activeCategory
      ? ['case', active, 7.5, 5]
      : 6
    const opacity: maplibregl.DataDrivenPropertyValueSpecification<number> = activeCategory
      ? ['case', active, 1, 0.25]
      : 1
    map.setPaintProperty('places', 'circle-radius', radius)
    map.setPaintProperty('places', 'circle-opacity', opacity)
    map.setPaintProperty('places', 'circle-stroke-opacity', opacity)
  }, [activeCategory, styleVersion])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !styleVersion || !styleReady.current) return
    const color = (target && PLACE_COLORS[target.category]) ?? FALLBACK_COLOR
    void map.getSource<maplibregl.GeoJSONSource>('route')?.setData(route ? route.feature : EMPTY)
    void map
      .getSource<maplibregl.GeoJSONSource>('target')
      ?.setData(target ? placesGeojson([target]) : EMPTY)
    map.setPaintProperty('route-line', 'line-color', color)
    map.setPaintProperty('target', 'circle-color', color)
  }, [route, target, styleVersion])

  // Show the whole route when a new one arrives (not when only the theme changes). Before
  // the first load, the load handler does it.
  useEffect(() => {
    const map = mapRef.current
    if (map && route && loadedRef.current) fitRoute(map, report, route)
  }, [route, report])

  return (
    <figure className="map-figure">
      <div ref={frame} className="map-frame">
        <div ref={container} className="map" />
        {children}
      </div>
      <figcaption className="visually-hidden">
        Karta s područjima do kojih se stiže pješice za 5, 10 i 15 minuta te ustanovama u
        blizini. Isti podaci navedeni su u tekstu uz kartu.
      </figcaption>
    </figure>
  )
}
