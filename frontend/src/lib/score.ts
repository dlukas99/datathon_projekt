import type { Category } from './api'

export interface ScoreResult {
  score: number | null
  up: { id: string; title: string; subscore: number } | null
  down: { id: string; title: string; subscore: number } | null
}

/** Weighted average of category sub-scores (0–100); categories without one are skipped. */
export function lifeScore(categories: Category[], weights: Record<string, number>): ScoreResult {
  const used = categories.filter(
    (c) => typeof c.subscore === 'number' && (weights[c.id] ?? 0) > 0,
  ) as (Category & { subscore: number })[]
  const total = used.reduce((sum, c) => sum + (weights[c.id] ?? 0), 0)
  if (total === 0) return { score: null, up: null, down: null }
  const score = Math.round(used.reduce((sum, c) => sum + c.subscore * (weights[c.id] ?? 0), 0) / total)
  // Pull of each category on the score: weight times distance from the average.
  const pulls = used.map((c) => ({ c, pull: (weights[c.id] ?? 0) * (c.subscore - score) }))
  const best = pulls.reduce((a, b) => (b.pull > a.pull ? b : a))
  const worst = pulls.reduce((a, b) => (b.pull < a.pull ? b : a))
  const pick = (x: { c: Category & { subscore: number } }) => ({
    id: x.c.id,
    title: x.c.title,
    subscore: x.c.subscore,
  })
  return {
    score,
    up: best.pull > 0 ? pick(best) : null,
    down: worst.pull < 0 ? pick(worst) : null,
  }
}

/** "flood-3.air-2" <-> { flood: 3, air: 2 } for the URL. */
export function encodeWeights(w: Record<string, number>): string {
  return Object.entries(w)
    .map(([k, v]) => `${k}-${String(v)}`)
    .join('.')
}

export function decodeWeights(text: string | null): Record<string, number> | null {
  if (!text) return null
  const out: Record<string, number> = {}
  for (const part of text.split('.')) {
    const [k, v] = part.split('-')
    const n = Number(v)
    if (k && Number.isFinite(n)) out[k] = Math.max(0, Math.min(3, n))
  }
  return Object.keys(out).length > 0 ? out : null
}
