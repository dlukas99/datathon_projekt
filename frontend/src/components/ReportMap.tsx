import { useEffect, useRef } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import type { Place, Report } from '../lib/api'

// The bundler moves maplibre's module away from its worker file; point to it explicitly.
maplibregl.setWorkerUrl(workerUrl)

const STYLES = {
  light: 'https://tiles.openfreemap.org/styles/positron',
  dark: 'https://tiles.openfreemap.org/styles/dark',
}

export const ISOCHRONE_COLORS: Record<number, string> = {
  5: '#1f7a4d',
  10: '#3f8fbf',
  15: '#8a6fbf',
}

export const PLACE_COLORS: Record<string, string> = {
  park: '#2e8b57',
  grocery: '#c0662b',
  pharmacy: '#c23b5a',
  doctor: '#b03030',
  pediatrician: '#d4508a',
  kindergarten: '#d9a400',
  school: '#7a52b3',
  playground: '#2a9d8f',
  stop: '#2f5fa8',
}

export const PLACE_NAMES: Record<string, string> = {
  park: 'park',
  grocery: 'trgovina namirnicama',
  pharmacy: 'ljekarna',
  doctor: 'obiteljski liječnik',
  pediatrician: 'pedijatar',
  kindergarten: 'vrtić',
  school: 'osnovna škola',
  playground: 'igralište',
  stop: 'stajalište',
}

function placesGeojson(places: Place[]): GeoJSON.FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: places.map((p) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [p.lon, p.lat] },
      properties: { category: p.category, name: p.name },
    })),
  }
}

function currentTheme(): 'light' | 'dark' {
  return document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'
}

export function ReportMap({ report, places }: { report: Report; places: Place[] }) {
  const container = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!container.current) return
    let map: maplibregl.Map
    try {
      map = new maplibregl.Map({
        container: container.current,
        style: STYLES[currentTheme()],
        center: [report.location.lon, report.location.lat],
        zoom: 14.5,
        attributionControl: { compact: false },
        cooperativeGestures: true,
      })
    } catch {
      // WebGL is not available (old device or test browser); the text equivalent remains.
      return
    }
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    map.on('load', () => {
      const iso = report.isochrones
      if (iso) {
        map.addSource('iso', { type: 'geojson', data: iso as GeoJSON.FeatureCollection })
        for (const minutes of [15, 10, 5]) {
          const color = ISOCHRONE_COLORS[minutes] ?? '#888'
          map.addLayer({
            id: `iso-${String(minutes)}`,
            type: 'fill',
            source: 'iso',
            filter: ['==', ['get', 'minutes'], minutes],
            paint: { 'fill-color': color, 'fill-opacity': 0.14 },
          })
          map.addLayer({
            id: `iso-line-${String(minutes)}`,
            type: 'line',
            source: 'iso',
            filter: ['==', ['get', 'minutes'], minutes],
            paint: { 'line-color': color, 'line-width': 2 },
          })
        }
        const bounds = new maplibregl.LngLatBounds()
        for (const f of iso.features) {
          const rings =
            f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates
          for (const poly of rings) for (const ring of poly) for (const c of ring) bounds.extend(c as maplibregl.LngLatLike)
        }
        if (!bounds.isEmpty()) map.fitBounds(bounds, { padding: 24, duration: 0 })
      }
      map.addSource('places', { type: 'geojson', data: placesGeojson(places) })
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
            '#666',
          ] as unknown as maplibregl.ExpressionSpecification,
          'circle-stroke-width': 1.5,
          'circle-stroke-color': '#ffffff',
        },
      })
    })
    new maplibregl.Marker({ color: '#1d2321' })
      .setLngLat([report.location.lon, report.location.lat])
      .addTo(map)
    return () => {
      map.remove()
    }
  }, [report, places])

  return (
    <figure style={{ margin: 0 }}>
      <div ref={container} className="map" />
      <figcaption className="visually-hidden">
        Karta s područjima do kojih se stiže pješice za 5, 10 i 15 minuta te ustanovama u
        blizini. Isti podaci navedeni su u tekstu uz kartu.
      </figcaption>
    </figure>
  )
}
