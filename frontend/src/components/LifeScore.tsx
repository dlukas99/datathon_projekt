import type { Category } from '../lib/api'
import { SCORE_CATEGORIES } from '../lib/profiles'
import type { ScoreResult } from '../lib/score'

const WEIGHT_WORDS = ['ne računa se', 'malo važno', 'važno', 'vrlo važno']

export function ScoreBadge({ result }: { result: ScoreResult }) {
  if (result.score === null) return null
  return (
    <a className="score-badge" href="#skor">
      <span className="score-badge-number">{result.score}</span>
      <span className="score-badge-text">Skor za život</span>
    </a>
  )
}

export function LifeScore({
  categories,
  weights,
  result,
  profileLabel,
  customised,
  onWeight,
  onReset,
}: {
  categories: Category[]
  weights: Record<string, number>
  result: ScoreResult
  profileLabel: string
  customised: boolean
  onWeight: (id: string, value: number) => void
  onReset: () => void
}) {
  const byId = Object.fromEntries(categories.map((c) => [c.id, c]))
  return (
    <section id="skor" className="section card life-score" aria-labelledby="score-title">
      <div className="life-score-head">
        <div>
          <h2 id="score-title">Skor za život</h2>
          <p className="hint">
            Prosjek kategorija ponderiran težinama za profil „{profileLabel}”
            {customised ? ' (prilagođeno)' : ''}. Vrijednosti kategorija se ne mijenjaju, samo
            njihova važnost.
          </p>
        </div>
        <p className="life-score-number" aria-live="polite">
          {result.score === null ? '–' : result.score}
          <span>/100</span>
        </p>
      </div>
      {(result.up ?? result.down) && (
        <p>
          {result.up && (
            <>
              Najviše podiže: <strong>{result.up.title}</strong> ({result.up.subscore}/100).{' '}
            </>
          )}
          {result.down && (
            <>
              Najviše spušta: <strong>{result.down.title}</strong> ({result.down.subscore}/100).
            </>
          )}
        </p>
      )}
      <fieldset className="weights no-print">
        <legend>Težine (0–3)</legend>
        {SCORE_CATEGORIES.map((c) => {
          const w = weights[c.id] ?? 0
          const sub = byId[c.id]?.subscore
          const id = `w-${c.id}`
          return (
            <div key={c.id} className="weight-row">
              <label htmlFor={id}>
                {c.label}
                <span className="weight-sub">
                  {typeof sub === 'number' ? `${String(sub)}/100` : 'nema podskora'}
                </span>
              </label>
              <input
                id={id}
                type="range"
                min={0}
                max={3}
                step={1}
                value={w}
                aria-valuetext={`${String(w)}, ${WEIGHT_WORDS[w] ?? ''}`}
                onChange={(e) => {
                  onWeight(c.id, Number(e.target.value))
                }}
              />
              <span className="weight-value">{WEIGHT_WORDS[w]}</span>
            </div>
          )
        })}
        {customised && (
          <button type="button" className="button ghost" onClick={onReset}>
            Vrati težine profila
          </button>
        )}
      </fieldset>
      <p className="hint">
        Kako se računaju podskorovi i zašto: <a href="/o-alatu#kako-racunamo">Kako računamo</a>.
      </p>
    </section>
  )
}
