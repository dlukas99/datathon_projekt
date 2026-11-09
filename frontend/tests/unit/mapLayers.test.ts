import { describe, expect, it } from 'vitest'
import { columnsToTable, type MapRow } from '../../src/lib/api'
import {
  LAYERS,
  featureState,
  getLayer,
  matches,
  needsClass,
  scoreClass,
  sortRows,
  transitClass,
} from '../../src/lib/mapLayers'
import { decodeGeometry } from '../../src/lib/settlementGeometry'

function row(over: Partial<MapRow>): MapRow {
  return {
    id: 1,
    code: '000001',
    name: 'Đakovo',
    municipality: 'Đakovo',
    county: 'Osječko-baranjska županija',
    population: 18000,
    lat: 45.3,
    lon: 18.4,
    air: 'umjerena',
    pm25: 14,
    flood: 'good',
    tree: 12,
    nature: 40,
    urban: 0.6,
    needs: 6,
    departures: null,
    stops: true,
    scores: { opci: 70, obitelj: 64, umirovljenik: 72, student: 60, 'rad-od-kuce': 75 },
    ...over,
  }
}

describe('map layer classes', () => {
  it('uses the report air ratings, weakest first', () => {
    const air = getLayer('air')
    expect(air.classes.map((c) => c.label)).toEqual(['Loš', 'Umjeren', 'Dobar', 'Vrlo dobar'])
    expect(air.classOf(row({ air: 'vrlo niska' }), 'opci')).toBe(3)
    expect(air.classOf(row({ air: null }), 'opci')).toBeNull()
  })

  it('bins the score in steps of 20 and needs in pairs', () => {
    expect([0, 19, 20, 59, 60, 80, 100].map(scoreClass)).toEqual([0, 0, 1, 2, 3, 4, 4])
    expect([0, 1, 2, 3, 4, 5, 6, 7].map(needsClass)).toEqual([0, 0, 1, 1, 2, 2, 3, 3])
  })

  it('tells stops without a timetable from no stops and from frequent service', () => {
    expect(transitClass(row({ stops: false }))).toBe(0)
    expect(transitClass(row({ stops: true }))).toBe(1)
    expect(transitClass(row({ departures: 0.5 }))).toBe(2)
    expect(transitClass(row({ departures: 3 }))).toBe(3)
    expect(transitClass(row({ departures: 6 }))).toBe(4)
    // Without the walking network the value is unknown, not "no stops".
    expect(transitClass(row({ needs: null, stops: false }))).toBeNull()
  })

  it('stores a class for every layer and map profile in feature state', () => {
    const state = featureState(row({}))
    expect(state.score_opci).toBe(3)
    expect(state['score_rad-od-kuce']).toBe(3)
    expect(state.air).toBe(1)
    expect(state.flood).toBe(4)
    expect(state.needs).toBe(4)
    expect(state.transit).toBe(1)
    expect(Object.keys(featureState(row({ air: null, flood: null })))).not.toContain('air')
  })

  it('gives every layer a legend that fits the five-step palette', () => {
    for (const l of LAYERS) {
      for (const c of l.classes) expect(c.step).toBeGreaterThanOrEqual(0)
      for (const c of l.classes) expect(c.step).toBeLessThan(5)
    }
  })
})

describe('settlement table', () => {
  const rows = [
    row({ id: 1, name: 'Aselo', scores: { opci: 50 } }),
    row({ id: 2, name: 'Bgrad', scores: { opci: 80 } }),
    row({ id: 3, name: 'Čakovec', scores: { opci: null } }),
  ]

  it('sorts by the layer, missing values last in both directions', () => {
    const score = getLayer('score')
    expect(sortRows(rows, score, 'opci', true).map((r) => r.id)).toEqual([2, 1, 3])
    expect(sortRows(rows, score, 'opci', false).map((r) => r.id)).toEqual([1, 2, 3])
  })

  it('finds names without diacritics', () => {
    expect(matches(row({}), 'dakovo')).toBe(true)
    expect(matches(row({ name: 'Čakovec', municipality: 'Čakovec' }), 'cakov')).toBe(true)
    expect(matches(row({}), 'split')).toBe(false)
  })
})

describe('settlement table by columns', () => {
  it('turns one list per field back into rows, with the six-digit code', () => {
    const t = columnsToTable({
      id: [35, 69248],
      name: ['Adžamovci', 'Vinkovci'],
      municipality: ['Rešetari', 'Vinkovci'],
      county: ['Brodsko-posavska županija', 'Vukovarsko-srijemska županija'],
      population: [446, null],
      lat: [45.2513, 45.2884],
      lon: [17.4619, 18.8045],
      air: ['umjerena', 'umjerena'],
      pm25: [15.7, 14.2],
      flood: ['good', 'good'],
      tree: [24.2, 7.1],
      nature: [80.5, 9.3],
      urban: [0, 1],
      needs: [1, 6],
      departures: [null, null],
      stops: [false, true],
      scores: { opci: [55, 68], obitelj: [50, null] },
      profiles_date: '2026-11-07T18:00:00+00:00',
      sources: {},
    })
    expect(t.rows).toHaveLength(2)
    expect(t.rows[0]?.code).toBe('000035')
    expect(t.rows[1]?.population).toBeNull()
    expect(t.rows[1]?.scores).toEqual({ opci: 68, obitelj: null })
    expect(t.rows[1]?.stops).toBe(true)
  })
})

describe('compact geometry', () => {
  it('decodes delta-encoded rings to GeoJSON with the settlement id', () => {
    const fc = decodeGeometry({
      step: 0.001,
      features: [[69248, [[[15000, 45000, 10, 0, 0, 10, -10, 0, 0, -10]]]]],
    })
    const f = fc.features[0]
    expect(f?.id).toBe(69248)
    const coords = (f?.geometry as GeoJSON.MultiPolygon).coordinates[0]?.[0]
    expect(coords?.[0]?.[0]).toBeCloseTo(15)
    expect(coords?.[2]?.[0]).toBeCloseTo(15.01)
    expect(coords?.[2]?.[1]).toBeCloseTo(45.01)
    expect(coords?.[4]).toEqual(coords?.[0])
  })
})
