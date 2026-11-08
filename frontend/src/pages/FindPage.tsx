import { useMutation, useQuery } from '@tanstack/react-query'
import { ArrowLeft, ArrowRight, Check, Minus } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { ListingLinks } from '../components/ListingLinks'
import { type FindRequest, fetchFindOptions, findPlaces, parseFindQuestion } from '../lib/api'
import { finderRationale, finderSummary } from '../lib/finderRules'
import { PROFILES, SCORE_CATEGORIES, profileWeights } from '../lib/profiles'
import { decodeWeights, encodeWeights } from '../lib/score'
import { reportPath } from '../lib/urls'

type Need = FindRequest['must'][number]

const NEEDS: { id: Need; label: string }[] = [
  { id: 'kindergarten', label: 'Vrtić' },
  { id: 'school', label: 'Osnovna škola' },
  { id: 'doctor', label: 'Obiteljski liječnik' },
  { id: 'pediatrician', label: 'Pedijatar' },
  { id: 'pharmacy', label: 'Ljekarna' },
  { id: 'grocery', label: 'Trgovina' },
  { id: 'park', label: 'Park' },
  { id: 'transit', label: 'Prijevoz svaki sat' },
]

const STEPS = ['Tko traži', 'Gdje', 'Što je važno', 'Prijedlozi'] as const
const LAST = STEPS.length
const SIZES: FindRequest['size'][] = ['any', 'village', 'town', 'city']
const AIRS: FindRequest['max_air'][] = ['any', 'umjerena', 'niska']
const WEIGHT_WORDS = ['nevažno', 'malo', 'srednje', 'jako']
const FIND_PROFILES = PROFILES.filter((p) => p.id !== 'vlastiti')

function oneOf<T extends string>(value: string | null, options: readonly T[], fallback: T): T {
  return options.find((o) => o === value) ?? fallback
}

/** The whole question lives in the URL: back retraces the path, a link restores it. */
function readRequest(params: URLSearchParams): FindRequest {
  const profile = params.get('profil') ?? 'opci'
  const needs = NEEDS.map((n) => n.id)
  return {
    profile: FIND_PROFILES.some((p) => p.id === profile) ? profile : 'opci',
    weights: decodeWeights(params.get('tezine')),
    county: params.get('podrucje'),
    size: oneOf(params.get('velicina'), SIZES, 'any'),
    must: (params.get('mora') ?? '').split(',').filter((m): m is Need => needs.includes(m as Need)),
    max_air: oneOf(params.get('zrak'), AIRS, 'any'),
    avoid_flood: params.get('poplave') === 'ne',
    limit: 10,
  }
}

function writeRequest(r: FindRequest, step: number): URLSearchParams {
  const p = new URLSearchParams()
  if (step > 1) p.set('korak', String(step))
  if (r.profile !== 'opci') p.set('profil', r.profile)
  if (r.weights) p.set('tezine', encodeWeights(r.weights))
  if (r.county) p.set('podrucje', r.county)
  if (r.size !== 'any') p.set('velicina', r.size)
  if (r.must.length > 0) p.set('mora', r.must.join(','))
  if (r.max_air !== 'any') p.set('zrak', r.max_air)
  if (r.avoid_flood) p.set('poplave', 'ne')
  return p
}

export function FindPage() {
  const [params, setParams] = useSearchParams()
  const step = Math.min(LAST, Math.max(1, Number(params.get('korak')) || 1))
  // The answers in local state, kept in step with the URL: a controlled checkbox must not
  // wait for the navigation, and back/forward still restores what the URL says.
  const search = params.toString()
  const [form, setForm] = useState<FindRequest>(() => readRequest(params))
  // The URL last seen, and the one this page last wrote. Only a URL the page did not write
  // (back, forward, a pasted link) replaces the answers; until a write lands, the URL still
  // shows the old answers and must not undo the new ones.
  const [seen, setSeen] = useState(search)
  const [written, setWritten] = useState(search)
  if (search !== seen) {
    setSeen(search)
    if (search !== written) setForm(readRequest(params))
  }
  const [question, setQuestion] = useState('')
  // Which way the trail was walked, for the direction of the step transition.
  const [walked, setWalked] = useState({ from: step, to: step })
  if (walked.to !== step) setWalked({ from: walked.to, to: step })
  const direction = walked.to >= walked.from ? 'forward' : 'back'
  const headingRef = useRef<HTMLHeadingElement>(null)
  const focusedStep = useRef(step)

  const options = useQuery({
    queryKey: ['find-options'],
    queryFn: ({ signal }) => fetchFindOptions(signal),
  })
  const results = useQuery({
    queryKey: ['find', form],
    queryFn: () => findPlaces(form),
    enabled: step === LAST,
    staleTime: 5 * 60_000,
  })
  const parse = useMutation({
    mutationFn: parseFindQuestion,
    onSuccess: (filters) => {
      go(LAST, { ...form, ...filters, limit: 10 })
    },
  })

  // A new step moves keyboard and screen-reader focus to its question (not on first load).
  useEffect(() => {
    if (focusedStep.current === step) return
    focusedStep.current = step
    headingRef.current?.focus()
  }, [step])

  function go(next: number, request: FindRequest = form) {
    const p = writeRequest(request, next)
    setWritten(p.toString())
    setForm(request)
    setParams(p)
  }

  function update(change: Partial<FindRequest>) {
    const request = { ...form, ...change }
    const p = writeRequest(request, step)
    setWritten(p.toString())
    setForm(request)
    setParams(p, { replace: true })
  }

  const weights = { ...profileWeights(form.profile), ...(form.weights ?? {}) }

  return (
    <div className="wizard">
      <h1>Gdje bih mogao živjeti?</h1>
      {step === 1 && (
        <p className="lead left">
          Tri kratka pitanja, a aplikacija predlaže naselja u kojima je ispunjeno ono što vam je
          važno, s razlozima i poveznicom na cijeli izvještaj.
        </p>
      )}

      <nav className="trail" aria-label="Koraci">
        <p className="eyebrow trail-name">Predloži mjesto za život</p>
        <p className="trail-count" aria-live="polite">
          {step < LAST ? `Pitanje ${String(step)} od ${String(LAST - 1)}` : 'Prijedlozi'}
        </p>
        <ol className="trail-stations">
          {STEPS.map((title, i) => {
            const n = i + 1
            const state = n < step ? 'done' : n === step ? 'current' : 'next'
            return (
              <li key={title} className="trail-station" data-state={state}>
                {state === 'done' ? (
                  <button
                    type="button"
                    onClick={() => {
                      go(n)
                    }}
                  >
                    <span className="trail-dot" aria-hidden="true">
                      <Check size={16} strokeWidth={3} />
                    </span>
                    <span className="trail-label">
                      {title}
                      <span className="visually-hidden"> (gotovo, promijeni)</span>
                    </span>
                  </button>
                ) : (
                  <span aria-current={state === 'current' ? 'step' : undefined}>
                    <span className="trail-dot" aria-hidden="true">
                      {n}
                    </span>
                    <span className="trail-label">{title}</span>
                  </span>
                )}
              </li>
            )
          })}
        </ol>
      </nav>

      <section
        key={step}
        className="wizard-step"
        data-direction={direction}
        aria-labelledby="step-title"
      >
        {step === 1 && (
          <form
            onSubmit={(e) => {
              e.preventDefault()
              go(2)
            }}
          >
            <fieldset className="choice-set">
              <legend>
                <h2 id="step-title" ref={headingRef} tabIndex={-1}>
                  Tko traži dom?
                </h2>
              </legend>
              <p className="step-intro">
                Profil određuje obavezne uvjete i što podiže rang mjesta, nikad same vrijednosti.
              </p>
              <div className="choices">
                {FIND_PROFILES.map((p) => (
                  <label key={p.id} className="choice">
                    <input
                      type="radio"
                      name="profile"
                      value={p.id}
                      checked={form.profile === p.id}
                      onChange={() => {
                        update({ profile: p.id, weights: null })
                      }}
                    />
                    <span className="choice-title">{p.label}</span>
                    <span className="choice-text">{finderSummary(p.id)}</span>
                  </label>
                ))}
              </div>
            </fieldset>
            <div className="wizard-nav">
              <button type="submit" className="button">
                Dalje <ArrowRight size={18} aria-hidden="true" />
              </button>
            </div>

            {options.data?.llm && (
              <div className="find-ask">
                <label htmlFor="find-question">Radije opisujete svojim riječima?</label>
                <div className="assistant-form">
                  <input
                    id="find-question"
                    type="text"
                    maxLength={300}
                    placeholder="npr. manje mjesto u Osječko-baranjskoj s vrtićem i školom, bez poplava"
                    value={question}
                    onChange={(e) => {
                      setQuestion(e.target.value)
                    }}
                  />
                  <button
                    type="button"
                    className="button secondary"
                    disabled={parse.isPending}
                    onClick={() => {
                      if (question.trim().length >= 3) parse.mutate(question.trim())
                    }}
                  >
                    {parse.isPending ? 'Tumačim…' : 'Pretvori u uvjete'}
                  </button>
                </div>
                <p className="hint">
                  Jezični model samo popunjava uvjete; rang i brojke računa aplikacija.
                </p>
                {parse.isError && <p role="alert">{parse.error.message}</p>}
              </div>
            )}
          </form>
        )}

        {step === 2 && (
          <form
            onSubmit={(e) => {
              e.preventDefault()
              go(3)
            }}
          >
            <h2 id="step-title" ref={headingRef} tabIndex={-1}>
              Gdje tražite?
            </h2>
            <p className="step-intro">Ostavite „Cijela Hrvatska” ako vam je mjesto svejedno.</p>
            <div className="find-grid">
              <label>
                Područje
                <select
                  value={form.county ?? ''}
                  onChange={(e) => {
                    update({ county: e.target.value || null })
                  }}
                >
                  <option value="">Cijela Hrvatska</option>
                  {options.data?.counties.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Veličina mjesta
                <select
                  value={form.size}
                  onChange={(e) => {
                    update({ size: oneOf(e.target.value, SIZES, 'any') })
                  }}
                >
                  <option value="any">Bilo koja</option>
                  <option value="village">Manje mjesto (do 2.000)</option>
                  <option value="town">Gradić (2.000–20.000)</option>
                  <option value="city">Grad (više od 20.000)</option>
                </select>
              </label>
            </div>
            <div className="wizard-nav">
              <button
                type="button"
                className="button ghost"
                onClick={() => {
                  go(1)
                }}
              >
                <ArrowLeft size={18} aria-hidden="true" /> Natrag
              </button>
              <button type="submit" className="button">
                Dalje <ArrowRight size={18} aria-hidden="true" />
              </button>
            </div>
          </form>
        )}

        {step === 3 && (
          <form
            onSubmit={(e) => {
              e.preventDefault()
              go(4)
            }}
          >
            <h2 id="step-title" ref={headingRef} tabIndex={-1}>
              Što vam je važno?
            </h2>
            <fieldset className="profiles find-env">
              <legend>Okoliš</legend>
              <div className="find-env-row">
                <label className="chip find-flood">
                  <input
                    type="checkbox"
                    checked={form.avoid_flood}
                    onChange={(e) => {
                      update({ avoid_flood: e.target.checked })
                    }}
                  />
                  Izvan modeliranih poplavnih područja
                </label>
                <label className="find-air">
                  Zrak
                  <select
                    value={form.max_air}
                    onChange={(e) => {
                      update({ max_air: oneOf(e.target.value, AIRS, 'any') })
                    }}
                  >
                    <option value="any">Bilo koji</option>
                    <option value="umjerena">Umjeren ili bolji</option>
                    <option value="niska">Dobar ili bolji</option>
                  </select>
                </label>
              </div>
            </fieldset>
            <fieldset className="profiles">
              <legend>Pješice do 15 minuta mora biti</legend>
              <div className="chips">
                {NEEDS.map((n) => (
                  <label key={n.id} className="chip">
                    <input
                      type="checkbox"
                      checked={form.must.includes(n.id)}
                      onChange={(e) => {
                        update({
                          must: e.target.checked
                            ? [...form.must, n.id]
                            : form.must.filter((m) => m !== n.id),
                        })
                      }}
                    />
                    {n.label}
                  </label>
                ))}
              </div>
            </fieldset>
            <details className="advanced">
              <summary>Napredno: težine u Skoru za život</summary>
              <div className="advanced-body">
                <fieldset className="find-weights">
                  <legend>Koliko je što važno u Skoru za život</legend>
                  {SCORE_CATEGORIES.map((c) => {
                    const w = weights[c.id] ?? 0
                    return (
                      <label key={c.id} className="find-weight">
                        <span>{c.label}</span>
                        <input
                          type="range"
                          min={0}
                          max={3}
                          step={1}
                          value={w}
                          aria-valuetext={WEIGHT_WORDS[w]}
                          onChange={(e) => {
                            update({ weights: { ...weights, [c.id]: Number(e.target.value) } })
                          }}
                        />
                        <span className="weight-word">{WEIGHT_WORDS[w]}</span>
                      </label>
                    )
                  })}
                  {form.weights && (
                    <button
                      type="button"
                      className="button ghost"
                      onClick={() => {
                        update({ weights: null })
                      }}
                    >
                      Vrati težine profila
                    </button>
                  )}
                </fieldset>
              </div>
            </details>

            <div className="wizard-nav">
              <button
                type="button"
                className="button ghost"
                onClick={() => {
                  go(2)
                }}
              >
                <ArrowLeft size={18} aria-hidden="true" /> Natrag
              </button>
              <button type="submit" className="button">
                Predloži mjesta <ArrowRight size={18} aria-hidden="true" />
              </button>
            </div>
          </form>
        )}

        {step === LAST && (
          <div aria-live="polite" aria-busy={results.isPending}>
            {/* One heading for every state, so focus stays on it while results arrive. */}
            <h2 id="step-title" ref={headingRef} tabIndex={-1}>
              {results.data
                ? results.data.results.length > 0
                  ? `Najbolje ${String(results.data.results.length)} od ${results.data.matching.toLocaleString('hr-HR')} naselja`
                  : 'Nijedno naselje ne ispunjava sve uvjete'
                : results.isError
                  ? 'Prijedlozi trenutačno nisu dostupni'
                  : 'Tražim naselja…'}
            </h2>
            {results.isError && (
              <p className="error-box" role="alert">
                Pokušajte ponovno za koju minutu; uvjeti su sačuvani u adresi stranice.
              </p>
            )}
            {results.data && (
              <>
                <p className="find-rule">{finderRationale(form.profile)}</p>
                {results.data.relaxed_note && (
                  <p className="find-relaxed-note">{results.data.relaxed_note}</p>
                )}
                <p className="section-intro find-criteria">
                  {results.data.criteria.join(' · ')}{' '}
                  <button
                    type="button"
                    className="link-button"
                    onClick={() => {
                      go(3)
                    }}
                  >
                    Promijeni uvjete
                  </button>
                </p>
                {results.data.results.length === 0 && (
                  <p>Uklonite jedan od uvjeta ili proširite područje.</p>
                )}
                <ol className="find-results">
                  {results.data.results.map((r, i) => (
                    <li key={r.code} className="find-result">
                      <div className="find-head">
                        <span className="find-rank" aria-hidden="true">
                          {i + 1}
                        </span>
                        <h3>{r.name}</h3>
                        {r.score !== null && (
                          <span className="score-badge small">
                            <span className="score-badge-number">{r.score}</span>
                            <span className="score-badge-text">za profil</span>
                          </span>
                        )}
                        <p className="place-line">
                          {r.municipality !== r.name ? `${r.municipality}, ` : ''}
                          {r.county} · {r.population.toLocaleString('hr-HR')} stanovnika
                        </p>
                      </div>
                      {r.relaxed && (
                        <p className="find-relaxed">Ne ispunjava jedan uvjet profila</p>
                      )}
                      {r.met.length > 0 && (
                        <>
                          <h4 className="find-list-title">Zašto je predloženo</h4>
                          <ul className="find-checks">
                            {r.met.map((m) => (
                              <li key={m} className="find-met">
                                <Check size={16} aria-hidden="true" />
                                <span>{m}</span>
                              </li>
                            ))}
                          </ul>
                        </>
                      )}
                      {r.missing.length > 0 && (
                        <>
                          <h4 className="find-list-title">Što nedostaje</h4>
                          <ul className="find-checks">
                            {r.missing.map((m) => (
                              <li key={m} className="find-missing">
                                <Minus size={16} aria-hidden="true" />
                                <span>{m}</span>
                              </li>
                            ))}
                          </ul>
                        </>
                      )}
                      {r.reasons.length > 0 && (
                        <p className="find-reasons">{r.reasons.join(' · ')}</p>
                      )}
                      <ul className="notes">
                        {r.facts.map((f) => (
                          <li key={f}>{f}</li>
                        ))}
                      </ul>
                      <div className="button-row">
                        <Link
                          className="button"
                          to={reportPath(
                            r.lat,
                            r.lon,
                            `${r.name}, ${r.municipality}`,
                            form.profile,
                            [],
                            'settlement',
                          )}
                        >
                          Otvori izvještaj
                        </Link>
                        <ListingLinks
                          settlement={r.name}
                          municipality={r.municipality}
                          county={r.county}
                        />
                      </div>
                    </li>
                  ))}
                </ol>
                <p className="fine-print">{results.data.note}</p>
              </>
            )}
            <div className="wizard-nav">
              <button
                type="button"
                className="button ghost"
                onClick={() => {
                  go(3)
                }}
              >
                <ArrowLeft size={18} aria-hidden="true" /> Promijeni uvjete
              </button>
              <button
                type="button"
                className="button ghost"
                onClick={() => {
                  go(1, { ...form, county: null, size: 'any', must: [], max_air: 'any', avoid_flood: false, weights: null })
                }}
              >
                Kreni ispočetka
              </button>
            </div>
          </div>
        )}
      </section>
    </div>
  )
}
