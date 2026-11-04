import type { Category } from '../../src/lib/api'
import { decodeWeights, encodeWeights, lifeScore } from '../../src/lib/score'

const cat = (id: string, subscore: number | null): Category => ({
  id,
  group: 'environment',
  title: id,
  status: 'info',
  status_label: '',
  headline: '',
  values: [],
  places: [],
  notes: [],
  links: [],
  subscore,
})

test('weighted average, explanation of what pulls up and down', () => {
  const cats = [cat('flood', 100), cat('air', 50), cat('solar', null)]
  const r = lifeScore(cats, { flood: 1, air: 3, solar: 3 })
  expect(r.score).toBe(63)
  expect(r.up?.id).toBe('flood')
  expect(r.down?.id).toBe('air')
})

test('no weights gives no score', () => {
  expect(lifeScore([cat('flood', 100)], { flood: 0 }).score).toBeNull()
})

test('weights round-trip through the URL', () => {
  expect(decodeWeights(encodeWeights({ flood: 3, air: 0 }))).toEqual({ flood: 3, air: 0 })
  expect(decodeWeights('flood-9')).toEqual({ flood: 3 })
  expect(decodeWeights(null)).toBeNull()
})
