import { describe, expect, it } from 'vitest'
import { finderRationale, finderSummary } from '../../src/lib/finderRules'
import { PROFILES } from '../../src/lib/profiles'

describe('finder rules', () => {
  it('tells what every finder profile requires', () => {
    for (const p of PROFILES.filter((x) => x.id !== 'vlastiti')) {
      expect(finderSummary(p.id).length).toBeGreaterThan(10)
      expect(finderRationale(p.id).length).toBeGreaterThan(10)
    }
  })

  it('names studies for the student profile', () => {
    expect(finderSummary('student')).toMatch(/studij/)
  })

  it('falls back to the general profile', () => {
    expect(finderSummary('nepoznat')).toBe(finderSummary('opci'))
  })
})
