import type { Place } from '../../src/lib/api'
import { distanceSpoken, minutesSpoken, plural, wholeMinutes } from '../../src/lib/format'
import { categoryStats, nearestWord, placeTitle } from '../../src/lib/places'

function place(category: string, minutes: number | null, name = ''): Place {
  return {
    category,
    name,
    lat: 45,
    lon: 16,
    walk_minutes: minutes,
    distance_m: 100,
    source: 'test',
    retrieved_at: null,
    kind: 'modelled',
    detail: null,
  }
}

test('minutes are whole and at least one, as in the daily list', () => {
  expect(wholeMinutes(0.2)).toBe(1)
  expect(wholeMinutes(30.6)).toBe(31)
  expect(wholeMinutes(7.5)).toBe(8)
})

test('Croatian number agreement', () => {
  const minuta = (n: number) => plural(n, 'minuta', 'minute', 'minuta')
  expect([1, 2, 4, 5, 11, 12, 14, 21, 22, 25, 31, 104, 112].map(minuta)).toEqual([
    'minuta',
    'minute',
    'minute',
    'minuta',
    'minuta',
    'minuta',
    'minuta',
    'minuta',
    'minute',
    'minuta',
    'minuta',
    'minute',
    'minuta',
  ])
  expect(minutesSpoken(23.6)).toBe('24 minute')
  expect(distanceSpoken(2440)).toBe('2,4 kilometra')
  expect(distanceSpoken(2000)).toBe('2 kilometra')
  expect(distanceSpoken(5020)).toBe('5 kilometara')
  expect(distanceSpoken(1000)).toBe('1 kilometar')
  expect(distanceSpoken(854)).toBe('850 metara')
})

test('per-kind summary: count within 15 minutes, nearest and the three nearest', () => {
  const places = [
    place('kindergarten', 40, 'C'),
    place('kindergarten', 31, 'A'),
    place('kindergarten', 35, 'B'),
    place('kindergarten', 52, 'D'),
    place('grocery', 4, 'G'),
    place('grocery', 15, 'H'),
    place('grocery', null, 'not routed'),
  ]
  const kindergarten = categoryStats(places, 'kindergarten')
  expect(kindergarten.count15).toBe(0)
  expect(kindergarten.nearest?.name).toBe('A')
  expect(kindergarten.candidates.map((p) => p.name)).toEqual(['A', 'B', 'C'])
  const grocery = categoryStats(places, 'grocery')
  expect(grocery.count15).toBe(2)
  expect(grocery.candidates.map((p) => p.name)).toEqual(['G', 'H'])
  expect(categoryStats(places, 'pediatrician').nearest).toBeNull()
})

test('names and words for places', () => {
  expect(placeTitle(place('playground', 3, ''))).toBe('Igralište bez naziva')
  expect(placeTitle(place('school', 3, 'OŠ Ivana Gundulića'))).toBe('OŠ Ivana Gundulića')
  expect(nearestWord('kindergarten')).toBe('najbliži')
  expect(nearestWord('pharmacy')).toBe('najbliža')
  expect(nearestWord('stop')).toBe('najbliže')
})
