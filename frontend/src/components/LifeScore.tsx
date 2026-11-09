import { ChevronDown } from 'lucide-react'
import type { Category } from '../lib/api'
import { SCORE_CATEGORIES } from '../lib/profiles'
import type { ScoreResult } from '../lib/score'

/** Importance of a category for the rating, as people say it (weights 0–3 in the API). */
export const WEIGHT_WORDS = ['nije važno', 'malo važno', 'važno', 'vrlo važno']

/** A category's part of the rating in words; the 0–100 number stays in the details. */
export function subscoreWord(sub: number | null | undefined): string {
  if (typeof sub !== 'number') return 'nema podataka'
  if (sub >= 75) return 'dobro'
  if (sub >= 40) return 'osrednje'
  return 'slabo'
}

/** What lifts or lowers the rating most, in plain words instead of "Poplave (100/100)". */
const STRONG: Record<string, string> = {
  flood: 'nema opasnosti od riječnih poplava',
  air: 'čist zrak',
  green: 'puno prirode i hlada',
  noise: 'podalje od velikih cesta',
  fire: 'u blizini nije bilo većih požara raslinja',
  solar: 'puno sunca za panele',
  car_free: 'većina svakodnevnih potreba je pješice',
  transit: 'javni prijevoz vozi često',
  daily: 'usluge su blizu',
}
const WEAK: Record<string, string> = {
  flood: 'blizu je područje riječnih poplava',
  air: 'zrak je onečišćeniji',
  green: 'malo drveća i hlada',
  noise: 'blizu je velika cesta',
  fire: 'u blizini je bilo požara raslinja',
  solar: 'manje sunca za panele',
  car_free: 'za mnogo toga treba auto',
  transit: 'javni prijevoz vozi rijetko ili ga nema',
  daily: 'malo je usluga pješice',
}

export function strongText(id: string, sub: number): string {
  if (id === 'air' && sub < 100) return 'dobar zrak'
  if (id === 'car_free' && sub >= 100) return 'sve svakodnevne potrebe su pješice'
  return STRONG[id] ?? `${id} (${String(sub)})`
}

export function weakText(id: string, sub: number): string {
  if (id === 'flood' && sub === 0) return 'adresa je u području riječnih poplava'
  return WEAK[id] ?? `${id} (${String(sub)})`
}

export function ScoreBadge({ result }: { result: ScoreResult }) {
  if (result.score === null) return null
  return (
    <a className="score-badge" href="#ocjena">
      <span className="score-badge-number">{result.score}</span>
      <span className="score-badge-text">Ocjena mjesta</span>
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
    <section id="ocjena" className="section card life-score" aria-labelledby="score-title">
      <div className="life-score-head">
        <div>
          <h2 id="score-title">Ocjena mjesta</h2>
          <p className="life-score-sub">
            koliko odgovara vašim potrebama (profil: {profileLabel.toLowerCase()}
            {customised ? ', prilagođeno' : ''})
          </p>
        </div>
        <p className="life-score-number" aria-live="polite">
          {result.score === null ? '–' : result.score}
          <span> od 100</span>
        </p>
      </div>
      <p>Ocjena spaja sve kategorije prema tome koliko vam je koja važna.</p>
      {(result.up ?? result.down) && (
        <p className="life-score-why">
          {result.up && (
            <>
              <strong>Najbolje:</strong> {strongText(result.up.id, result.up.subscore)}.{' '}
            </>
          )}
          {result.down && (
            <>
              <strong>Najslabije:</strong> {weakText(result.down.id, result.down.subscore)}.
            </>
          )}
        </p>
      )}
      <details className="more weights-fold no-print">
        <summary>
          Prilagodi važnost <ChevronDown size={16} aria-hidden="true" className="chevron" />
        </summary>
        <fieldset className="weights">
          <legend>Koliko vam je važno</legend>
          {SCORE_CATEGORIES.map((c) => {
            const w = weights[c.id] ?? 0
            const sub = byId[c.id]?.subscore
            const id = `w-${c.id}`
            return (
              <div key={c.id} className="weight-row">
                <label htmlFor={id}>
                  {c.label}
                  <span className="weight-sub">
                    ovdje: {subscoreWord(sub)}
                    {typeof sub === 'number' && <span className="weight-num"> ({String(sub)} od 100)</span>}
                  </span>
                </label>
                <input
                  id={id}
                  type="range"
                  min={0}
                  max={3}
                  step={1}
                  value={w}
                  aria-valuetext={WEIGHT_WORDS[w] ?? ''}
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
              Vrati važnost iz profila
            </button>
          )}
        </fieldset>
      </details>
      <p className="hint">
        Kako se računa: <a href="/o-alatu#kako-racunamo">Kako računamo</a>.
      </p>
    </section>
  )
}
