import type { CompactGeometry } from './api'

/** Delta-encoded integer rings (backend/app/map_layer.py) to a GeoJSON collection. */
export function decodeGeometry(data: CompactGeometry): GeoJSON.FeatureCollection {
  const { step } = data
  const features: GeoJSON.Feature[] = data.features.map(([id, polygons]) => {
    const coordinates = polygons.map((rings) =>
      rings.map((ring) => {
        const out: [number, number][] = []
        let x = 0
        let y = 0
        for (let i = 0; i + 1 < ring.length; i += 2) {
          x += ring[i] ?? 0
          y += ring[i + 1] ?? 0
          out.push([x * step, y * step])
        }
        return out
      }),
    )
    return {
      type: 'Feature',
      id,
      properties: {},
      geometry: { type: 'MultiPolygon', coordinates },
    }
  })
  return { type: 'FeatureCollection', features }
}
