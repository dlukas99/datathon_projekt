import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import { fetchMapGeometry, type MapRow } from '../lib/api'
import { type LayerId, PALETTES, featureState, stateKey } from '../lib/mapLayers'
import { decodeGeometry } from '../lib/settlementGeometry'
import { type Theme, currentTheme, useDocumentTheme } from '../lib/useDocumentTheme'

maplibregl.setWorkerUrl(workerUrl)

const STYLES: Record<Theme, string> = {
  light: 'https://tiles.openfreemap.org/styles/positron',
  dark: 'https://tiles.openfreemap.org/styles/dark',
}
const OUTLINE: Record<Theme, string> = { light: '#ffffff', dark: '#111513' }
const SELECTED: Record<Theme, string> = { light: '#17201c', dark: '#ffffff' }
const CROATIA: [[number, number], [number, number]] = [
  [13.45, 42.35],
  [19.45, 46.56],
]
// The detailed outlines (80 m instead of 300 m) are loaded once the map is zoomed in.
const DETAIL_ZOOM = 8.5

const MAP_LOCALE: Record<string, string> = {
  'Map.Title': 'Karta',
  'NavigationControl.ZoomIn': 'Približi',
  'NavigationControl.ZoomOut': 'Udalji',
  'AttributionControl.ToggleAttribution': 'Prikaži ili sakrij izvore karte',
}
const ATTRIBUTION = 'Granice naselja: DGU (CC BY 4.0) · pokazatelji: izračun aplikacije'

export interface MapFocus {
  lat: number
  lon: number
  /** Changes whenever the map should move, even to the same place. */
  key: number
}

function fillColor(key: string, theme: Theme): maplibregl.ExpressionSpecification {
  const { steps, none } = PALETTES[theme]
  const cases = steps.flatMap((color, i) => [i, color])
  return [
    'match',
    ['coalesce', ['feature-state', key], -1],
    ...cases,
    none,
  ] as unknown as maplibregl.ExpressionSpecification
}

// Place names in Croatian where OpenStreetMap has them ("Hrvatska", not "Croatia").
const CROATIAN_NAME: maplibregl.ExpressionSpecification = [
  'coalesce',
  ['get', 'name:hr'],
  ['get', 'name:latin'],
  ['get', 'name'],
]

function showCroatianNames(map: maplibregl.Map) {
  for (const layer of map.getStyle().layers) {
    if (layer.type !== 'symbol') continue
    const field: unknown = map.getLayoutProperty(layer.id, 'text-field')
    if (JSON.stringify(field ?? '').includes('name_en')) {
      map.setLayoutProperty(layer.id, 'text-field', CROATIAN_NAME)
    }
  }
}

const EMPTY: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features: [] }

function firstSymbolLayer(map: maplibregl.Map): string | undefined {
  return map.getStyle().layers.find((l) => l.type === 'symbol')?.id
}

/**
 * Settlements of Croatia coloured by a precomputed layer. Colours sit in MapLibre feature
 * state, so switching the layer or profile only changes the paint, not the data.
 */
export function CroatiaMap({
  geometry,
  rows,
  layer,
  profile,
  selectedId,
  picked,
  focus,
  onPick,
  onReady,
}: {
  /** Overview outlines; null while they load (the base map is drawn meanwhile). */
  geometry: GeoJSON.FeatureCollection | null
  rows: MapRow[]
  layer: LayerId
  profile: string
  selectedId: number | null
  picked: { lat: number; lon: number } | null
  focus: MapFocus | null
  onPick: (lat: number, lon: number) => void
  onReady: () => void
}) {
  const container = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markerRef = useRef<maplibregl.Marker | null>(null)
  const ready = useRef(false)
  const data = useRef<GeoJSON.FeatureCollection>(geometry ?? EMPTY)
  // Which outlines the source holds; the detailed ones are never replaced by the overview.
  const level = useRef<'none' | 'overview' | 'detail'>(geometry ? 'overview' : 'none')
  const reported = useRef(false)
  const rowsRef = useRef(rows)
  const paint = useRef({ layer, profile })
  const selectedRef = useRef<number | null>(null)
  const onPickRef = useRef(onPick)
  const onReadyRef = useRef(onReady)
  const appliedTheme = useRef<Theme>('light')
  const [styleVersion, setStyleVersion] = useState(0)
  const [failed, setFailed] = useState(false)
  const theme = useDocumentTheme()

  useEffect(() => {
    onPickRef.current = onPick
    onReadyRef.current = onReady
    rowsRef.current = rows
    paint.current = { layer, profile }
  })

  useEffect(() => {
    if (!container.current) return
    let map: maplibregl.Map
    appliedTheme.current = currentTheme()
    try {
      map = new maplibregl.Map({
        container: container.current,
        style: STYLES[appliedTheme.current],
        bounds: CROATIA,
        fitBoundsOptions: { padding: 8 },
        minZoom: 5,
        maxZoom: 15,
        attributionControl: { compact: true, customAttribution: ATTRIBUTION },
        locale: MAP_LOCALE,
        dragRotate: false,
        pitchWithRotate: false,
      })
    } catch {
      // No WebGL (old device or test browser): the table below carries the same data.
      window.setTimeout(() => {
        setFailed(true)
        onReadyRef.current()
      }, 0)
      return
    }
    mapRef.current = map
    map.touchZoomRotate.disableRotation()
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')

    let detailRequested = false
    const loadDetail = () => {
      if (detailRequested || map.getZoom() < DETAIL_ZOOM) return
      detailRequested = true
      fetchMapGeometry('detail')
        .then((compact) => {
          data.current = decodeGeometry(compact)
          level.current = 'detail'
          void map.getSource<maplibregl.GeoJSONSource>('settlements')?.setData(data.current)
        })
        .catch(() => {
          detailRequested = false // keep the overview; try again on the next zoom
        })
    }

    map.on('style.load', () => {
      const t = appliedTheme.current
      showCroatianNames(map)
      const before = firstSymbolLayer(map)
      map.addSource('settlements', { type: 'geojson', data: data.current })
      map.addLayer(
        {
          id: 'settlements-fill',
          type: 'fill',
          source: 'settlements',
          paint: {
            'fill-color': fillColor(stateKey(paint.current.layer, paint.current.profile), t),
            'fill-opacity': ['interpolate', ['linear'], ['zoom'], 9, 0.82, 13, 0.5],
          },
        },
        before,
      )
      map.addLayer(
        {
          id: 'settlements-line',
          type: 'line',
          source: 'settlements',
          paint: {
            'line-color': OUTLINE[t],
            'line-opacity': 0.7,
            'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.15, 10, 0.8, 13, 1.4],
          },
        },
        before,
      )
      map.addLayer({
        id: 'settlements-selected',
        type: 'line',
        source: 'settlements',
        paint: {
          'line-color': SELECTED[t],
          'line-width': ['case', ['boolean', ['feature-state', 'selected'], false], 2.5, 0],
        },
      })
      for (const row of rowsRef.current) {
        map.setFeatureState({ source: 'settlements', id: row.id }, featureState(row))
      }
      if (selectedRef.current !== null) {
        map.setFeatureState({ source: 'settlements', id: selectedRef.current }, { selected: true })
      }
      ready.current = true
      setStyleVersion((v) => v + 1)
    })
    map.on('click', (e) => {
      onPickRef.current(e.lngLat.lat, e.lngLat.lng)
    })
    map.on('mousemove', 'settlements-fill', () => {
      map.getCanvas().style.cursor = 'pointer'
    })
    map.on('mouseleave', 'settlements-fill', () => {
      map.getCanvas().style.cursor = ''
    })
    map.on('zoomend', loadDetail)
    // The visible area, for tests that click a known place (data-bounds="w,s,e,n").
    const keepBounds = () => {
      const b = map.getBounds()
      map
        .getContainer()
        .setAttribute(
          'data-bounds',
          [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].map((v) => v.toFixed(6)).join(','),
        )
    }
    map.on('moveend', keepBounds)
    map.once('load', keepBounds)

    return () => {
      ready.current = false
      mapRef.current = null
      markerRef.current = null
      map.remove()
    }
  }, [])

  // The sun button in the header switches the base map; the overlays are added again.
  useEffect(() => {
    const map = mapRef.current
    if (!map || appliedTheme.current === theme) return
    appliedTheme.current = theme
    ready.current = false
    map.setStyle(STYLES[theme], { diff: false })
  }, [theme])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !ready.current) return
    if (geometry && level.current === 'none') {
      data.current = geometry
      level.current = 'overview'
      void map.getSource<maplibregl.GeoJSONSource>('settlements')?.setData(geometry)
    }
    for (const row of rows) {
      map.setFeatureState({ source: 'settlements', id: row.id }, featureState(row))
    }
    // Ready once the coloured settlements are drawn (MapLibre "idle": all tiles rendered).
    if (level.current !== 'none' && rows.length > 0 && !reported.current) {
      reported.current = true
      map.once('idle', () => {
        onReadyRef.current()
      })
    }
  }, [geometry, rows, styleVersion])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !ready.current) return
    map.setPaintProperty(
      'settlements-fill',
      'fill-color',
      fillColor(stateKey(layer, profile), appliedTheme.current),
    )
  }, [layer, profile, styleVersion])

  useEffect(() => {
    const map = mapRef.current
    const previous = selectedRef.current
    selectedRef.current = selectedId
    if (!map || !ready.current) return
    if (previous !== null && previous !== selectedId) {
      map.setFeatureState({ source: 'settlements', id: previous }, { selected: false })
    }
    if (selectedId !== null) {
      map.setFeatureState({ source: 'settlements', id: selectedId }, { selected: true })
    }
  }, [selectedId, styleVersion])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    if (!picked) {
      markerRef.current?.remove()
      markerRef.current = null
      return
    }
    if (!markerRef.current) {
      markerRef.current = new maplibregl.Marker({ color: SELECTED[theme] })
    }
    markerRef.current.setLngLat([picked.lon, picked.lat]).addTo(map)
    // On a phone the card opens as a sheet over the lower part of the map: keep the
    // picked point in the upper part.
    if (window.matchMedia('(width <= 760px)').matches) {
      const y = map.project([picked.lon, picked.lat]).y
      const target = map.getContainer().clientHeight * 0.3
      if (y > target) map.panBy([0, y - target], { duration: 300 })
    }
  }, [picked, theme])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !focus) return
    map.flyTo({ center: [focus.lon, focus.lat], zoom: Math.max(map.getZoom(), 11), duration: 700 })
  }, [focus])

  if (failed) {
    return (
      <div className="atlas-map atlas-map-failed" role="note">
        Karta se na ovom uređaju ne može prikazati. Isti podaci nalaze se u tablici ispod.
      </div>
    )
  }
  return (
    <div
      ref={container}
      className="atlas-map"
      role="region"
      aria-label="Karta naselja Hrvatske. Isti podaci nalaze se u tablici ispod karte."
    />
  )
}
